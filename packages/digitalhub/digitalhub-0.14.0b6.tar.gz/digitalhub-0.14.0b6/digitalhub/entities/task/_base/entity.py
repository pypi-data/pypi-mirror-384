# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.unversioned.entity import UnversionedEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import context_processor
from digitalhub.factory.entity import entity_factory

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.spec import TaskSpec
    from digitalhub.entities.task._base.status import TaskStatus


class Task(UnversionedEntity):
    """
    A class representing a task.
    """

    ENTITY_TYPE = EntityTypes.TASK.value

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: TaskSpec,
        status: TaskStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)
        self.spec: TaskSpec
        self.status: TaskStatus

    ##############################
    #  Task methods
    ##############################

    def run(
        self,
        run_kind: str,
        save: bool = True,
        local_execution: bool = False,
        **kwargs,
    ) -> Run:
        """
        Run task.

        Parameters
        ----------
        run_kind : str
            Kind the object.
        local_execution : bool
            Flag to indicate if the run will be executed locally.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        Run
            Run object.
        """
        exec_kind = entity_factory.get_executable_kind(self.kind)
        exec_type = entity_factory.get_entity_type_from_kind(exec_kind)
        kwargs[exec_type] = getattr(self.spec, exec_type)
        return self.new_run(
            save=save,
            project=self.project,
            task=self._get_task_string(),
            kind=run_kind,
            local_execution=local_execution,
            **kwargs,
        )

    def _get_task_string(self) -> str:
        """
        Get task string.

        Returns
        -------
        str
            Task string.
        """
        return f"{self.kind}://{self.project}/{self.id}"

    ##############################
    # CRUD Methods for Run
    ##############################

    def new_run(self, save: bool = True, **kwargs) -> Run:
        """
        Create a new run.

        Parameters
        ----------
        save : bool
            Flag to indicate save.
        **kwargs : dict
            Keyword arguments to build run. See new_run().

        Returns
        -------
        Run
            Run object.
        """
        if save:
            return context_processor.create_context_entity(**kwargs)
        return entity_factory.build_entity_from_params(**kwargs)

    def get_run(self, entity_key: str) -> Run:
        """
        Get run.

        Parameters
        ----------
        entity_key : str
            Entity key.

        Returns
        -------
        Run
            Run object.
        """
        return context_processor.read_context_entity(entity_key)

    def delete_run(self, entity_key: str) -> dict:
        """
        Delete run.

        Parameters
        ----------
        entity_key : str
            Entity key.

        Returns
        -------
        dict
            Response from backend.
        """
        return context_processor.delete_context_entity(entity_key)
