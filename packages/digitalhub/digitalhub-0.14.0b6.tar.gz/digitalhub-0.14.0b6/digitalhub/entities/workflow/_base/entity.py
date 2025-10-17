# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.executable.entity import ExecutableEntity
from digitalhub.entities._commons.enums import EntityTypes, Relationship
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import BackendError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.workflow._base.spec import WorkflowSpec
    from digitalhub.entities.workflow._base.status import WorkflowStatus


class Workflow(ExecutableEntity):
    """
    A class representing a workflow.
    """

    ENTITY_TYPE = EntityTypes.WORKFLOW.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: WorkflowSpec,
        status: WorkflowStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: WorkflowSpec
        self.status: WorkflowStatus

    ##############################
    #  Workflow Methods
    ##############################

    def run(
        self,
        action: str,
        wait: bool = False,
        log_info: bool = True,
        **kwargs,
    ) -> Run:
        """
        Run workflow.

        Parameters
        ----------
        action : str
            Action to execute.
        wait : bool
            Flag to wait for execution to finish.
        log_info : bool
            Flag to log information while waiting.
        **kwargs : dict
            Keyword arguments passed to Run builder.

        Returns
        -------
        Run
            Run instance.
        """
        # Get task and run kind
        task_kind = entity_factory.get_task_kind_from_action(self.kind, action)
        run_kind = entity_factory.get_run_kind_from_action(self.kind, action)

        # Create or update new task
        task = self._get_or_create_task(task_kind)

        # Raise error if execution is not done by DHCore backend
        if self._context().local:
            raise BackendError("Cannot run workflow with local backend.")

        # Run task
        run = task.run(run_kind, save=False, local_execution=False, **kwargs)

        # Set as run's parent
        run.add_relationship(Relationship.RUN_OF.value, self.key)
        run.save()

        if wait:
            return run.wait(log_info=log_info)
        return run
