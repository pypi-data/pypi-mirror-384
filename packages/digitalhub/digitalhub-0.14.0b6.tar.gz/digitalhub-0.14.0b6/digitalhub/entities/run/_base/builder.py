# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.runtime_entity.builder import EntityError, RuntimeEntityBuilder
from digitalhub.entities._base.unversioned.builder import UnversionedBuilder
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class RunBuilder(UnversionedBuilder, RuntimeEntityBuilder):
    """
    Run builder.
    """

    ENTITY_TYPE = EntityTypes.RUN.value

    def build(
        self,
        project: str,
        kind: str,
        uuid: str | None = None,
        labels: list[str] | None = None,
        task: str | None = None,
        local_execution: bool = False,
        **kwargs,
    ) -> Run:
        """
        Create a new object.

        Parameters
        ----------
        project : str
            Project name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        labels : list[str]
            List of labels.
        task : str
            Name of the task associated with the run.
        local_execution : bool
            Flag to determine if object has local execution.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Run
            Object instance.
        """
        # Check task validity
        if task is None:
            raise EntityError("Missing task in run spec")
        self._check_kind_validity(task)

        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=uuid,
            labels=labels,
        )
        spec = self.build_spec(
            task=task,
            local_execution=local_execution,
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            project=project,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )

    def _check_kind_validity(self, task: str) -> None:
        """
        Check kind validity.

        Parameters
        ----------
        task : str
            Task string.
        """
        task_kind = task.split("://")[0]
        if task_kind not in self.get_all_kinds():
            raise EntityError(f"Invalid run '{self.ENTITY_KIND}' for task kind '{task_kind}'")
