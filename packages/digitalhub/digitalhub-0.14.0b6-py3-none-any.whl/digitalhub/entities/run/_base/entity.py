# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
import typing

from digitalhub.entities._base.unversioned.entity import UnversionedEntity
from digitalhub.entities._commons.enums import EntityTypes, State
from digitalhub.entities._commons.metrics import MetricType, set_metrics, validate_metric_value
from digitalhub.entities._processors.processors import context_processor
from digitalhub.factory.entity import entity_factory
from digitalhub.factory.runtime import runtime_factory
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.logger import LOGGER

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.run._base.spec import RunSpec
    from digitalhub.entities.run._base.status import RunStatus
    from digitalhub.runtimes._base import Runtime


class Run(UnversionedEntity):
    """
    A class representing a run.
    """

    ENTITY_TYPE = EntityTypes.RUN.value

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpec,
        status: RunStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpec
        self.status: RunStatus

    ##############################
    #  Run Methods
    ##############################

    def build(self) -> None:
        """
        Build run.
        """
        executable = self._get_executable()
        task = self._get_task()
        new_spec = self._get_runtime().build(executable, task, self.to_dict())
        self.spec = entity_factory.build_spec(self.kind, **new_spec)
        self._set_state(State.BUILT.value)
        self.save(update=True)

    def run(self) -> Run:
        """
        Run run.

        Returns
        -------
        Run
            Run object.
        """
        self.refresh()

        self._start_execution()
        self._setup_execution()

        try:
            status = self._get_runtime().run(self.to_dict())
        except Exception as e:
            self.refresh()
            if self.spec.local_execution:
                self._set_state(State.ERROR.value)
            self._set_message(str(e))
            self.save(update=True)
            raise e
        finally:
            self._finish_execution()

        self.refresh()
        if not self.spec.local_execution:
            status.pop("state", None)
        new_status = {**self.status.to_dict(), **status}
        self._set_status(new_status)
        self.save(update=True)
        return self

    def wait(self, log_info: bool = True) -> Run:
        """
        Wait for run to finish.

        Parameters
        ----------
        log_info : bool
            If True, log information.

        Returns
        -------
        Run
            Run object.
        """
        start = time.time()
        while True:
            if log_info:
                LOGGER.info(f"Waiting for run {self.id} to finish...")
            self.refresh()
            time.sleep(5)
            if self.status.state in [
                State.STOPPED.value,
                State.ERROR.value,
                State.COMPLETED.value,
            ]:
                if log_info:
                    current = time.time() - start
                    LOGGER.info(f"Run {self.id} finished in {current:.2f} seconds.")
                return self

    def logs(self) -> dict:
        """
        Get run logs.

        Returns
        -------
        dict
            Run logs.
        """
        return context_processor.read_run_logs(self.project, self.ENTITY_TYPE, self.id)

    def stop(self) -> None:
        """
        Stop run.
        """
        if not self.spec.local_execution:
            return context_processor.stop_entity(self.project, self.ENTITY_TYPE, self.id)

    def resume(self) -> None:
        """
        Resume run.
        """
        if not self.spec.local_execution:
            return context_processor.resume_entity(self.project, self.ENTITY_TYPE, self.id)

    def log_metric(
        self,
        key: str,
        value: MetricType,
        overwrite: bool = False,
        single_value: bool = False,
    ) -> None:
        """
        Log metric into entity status.
        A metric is named by a key and value (single number or list of numbers).
        The metric by default is put in a list or appended to an existing list.
        If single_value is True, the value will be a single number.

        Parameters
        ----------
        key : str
            Key of the metric.
        value : MetricType
            Value of the metric.
        overwrite : bool
            If True, overwrite existing metric.
        single_value : bool
            If True, value is a single value.

        Examples
        --------
        Log a new value in a list
        >>> entity.log_metric("loss", 0.002)

        Append a new value in a list
        >>> entity.log_metric("loss", 0.0019)

        Log a list of values and append them to existing metric:
        >>> entity.log_metric(
        ...     "loss",
        ...     [
        ...         0.0018,
        ...         0.0015,
        ...     ],
        ... )

        Log a single value (not represented as list):
        >>> entity.log_metric(
        ...     "accuracy",
        ...     0.9,
        ...     single_value=True,
        ... )

        Log a list of values and overwrite existing metric:
        >>> entity.log_metric(
        ...     "accuracy",
        ...     [0.8, 0.9],
        ...     overwrite=True,
        ... )
        """
        self._set_metrics(key, value, overwrite, single_value)
        context_processor.update_metric(self.project, self.ENTITY_TYPE, self.id, key, self.status.metrics[key])

    def log_metrics(
        self,
        metrics: dict[str, MetricType],
        overwrite: bool = False,
    ) -> None:
        """
        Log metrics into entity status. If a metric is a list, it will be logged as a list.
        Otherwise, it will be logged as a single value.

        Parameters
        ----------
        metrics : dict[str, MetricType]
            Dict of metrics to log.
        overwrite : bool
            If True, overwrite existing metrics.

        Examples
        --------
        Log multiple metrics at once
        >>> entity.log_metrics(
        ...     {
        ...         "loss": 0.002,
        ...         "accuracy": 0.95,
        ...     }
        ... )

        Log metrics with lists and single values
        >>> entity.log_metrics(
        ...     {
        ...         "loss": [
        ...             0.1,
        ...             0.05,
        ...         ],
        ...         "epoch": 10,
        ...     }
        ... )

        Append to existing metrics (default behavior)
        >>> entity.log_metrics(
        ...     {
        ...         "loss": 0.001,
        ...         "accuracy": 0.96,
        ...     }
        ... )  # Appends to existing

        Overwrite existing metrics
        >>> entity.log_metrics(
        ...     {
        ...         "loss": 0.0005,
        ...         "accuracy": 0.98,
        ...     },
        ...     overwrite=True,
        ... )

        See also
        --------
        log_metric
        """
        for key, value in metrics.items():
            # For lists, use log_metric which handles appending correctly
            if isinstance(value, list):
                self.log_metric(key, value, overwrite)

            # For single values, check if we should append or create new
            else:
                if not overwrite and key in self.status.metrics:
                    self.log_metric(key, value)
                else:
                    self.log_metric(key, value, overwrite, single_value=True)

    ##############################
    #  Helpers
    ##############################

    def _setup_execution(self) -> None:
        """
        Setup run execution.
        """

    def _start_execution(self) -> None:
        """
        Start run execution.
        """
        self._context().set_run(f"{self.key}:{self.id}")
        if self.spec.local_execution:
            if not self._is_ready_to_run():
                raise EntityError("Run is not in a state to run.")
            self._set_state(State.RUNNING.value)
            self.save(update=True)

    def _finish_execution(self) -> None:
        """
        Finish run execution.
        """
        self._context().unset_run()

    def _is_ready_to_run(self) -> bool:
        """
        Check if run is in a state ready for running (BUILT or STOPPED).

        Returns
        -------
        bool
            True if run is in runnable state, False otherwise.
        """
        return self.status.state in (State.BUILT.value, State.STOPPED.value)

    def _set_status(self, status: dict) -> None:
        """
        Set run status.

        Parameters
        ----------
        status : dict
            Status to set.
        """
        self.status: RunStatus = entity_factory.build_status(self.kind, **status)

    def _set_state(self, state: str) -> None:
        """
        Update run state.

        Parameters
        ----------
        state : str
            State to set.
        """
        self.status.state = state

    def _set_message(self, message: str) -> None:
        """
        Update run message.

        Parameters
        ----------
        message : str
            Message to set.
        """
        self.status.message = message

    def _get_runtime(self) -> Runtime:
        """
        Build runtime to build run or execute it.

        Returns
        -------
        Runtime
            Runtime object.
        """
        return runtime_factory.build_runtime(self.kind, self.project)

    def _get_executable(self) -> dict:
        """
        Get executable object from backend. Reimplemented to avoid
        circular imports.

        Returns
        -------
        dict
            Executable (function or workflow) from backend.
        """
        exec_kind = entity_factory.get_executable_kind(self.kind)
        exec_type = entity_factory.get_entity_type_from_kind(exec_kind)
        string_to_split = getattr(self.spec, exec_type)
        exec_name, exec_id = string_to_split.split("://")[-1].split("/")[-1].split(":")
        return context_processor.read_context_entity(
            exec_name,
            entity_type=exec_type,
            project=self.project,
            entity_id=exec_id,
        ).to_dict()

    def _get_task(self) -> dict:
        """
        Get object from backend. Reimplemented to avoid
        circular imports.

        Returns
        -------
        dict
            Task from backend.
        """
        task_id = self.spec.task.split("://")[-1].split("/")[-1]
        return context_processor.read_unversioned_entity(
            task_id,
            entity_type=EntityTypes.TASK.value,
            project=self.project,
        ).to_dict()

    def _get_metrics(self) -> None:
        """
        Get model metrics from backend.
        """
        self.status.metrics = context_processor.read_metrics(
            project=self.project,
            entity_type=self.ENTITY_TYPE,
            entity_id=self.id,
        )

    def _set_metrics(
        self,
        key: str,
        value: MetricType,
        overwrite: bool,
        single_value: bool,
    ) -> None:
        """
        Set model metrics.

        Parameters
        ----------
        key : str
            Key of the metric.
        value : MetricType
            Value of the metric.
        overwrite : bool
            If True, overwrite existing metric.
        single_value : bool
            If True, value is a single value.
        """
        value = validate_metric_value(value)
        self.status.metrics = set_metrics(
            self.status.metrics,
            key,
            value,
            overwrite,
            single_value,
        )
