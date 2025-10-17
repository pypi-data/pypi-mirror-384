# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.runtime_entity.builder import EntityError, RuntimeEntityBuilder
from digitalhub.entities._base.unversioned.builder import UnversionedBuilder
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities.task._base.entity import Task


class TaskBuilder(UnversionedBuilder, RuntimeEntityBuilder):
    """
    Task builder.
    """

    ENTITY_TYPE = EntityTypes.TASK.value

    def build(
        self,
        project: str,
        kind: str,
        uuid: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> Task:
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
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Task
            Object instance.
        """
        # Check executable kind validity
        fnc = kwargs.get("function", None)
        wkf = kwargs.get("workflow", None)
        executable = fnc if fnc is not None else wkf
        if executable is None:
            raise EntityError("Function or workflow must be provided")
        self._check_kind_validity(executable)

        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=uuid,
            labels=labels,
        )
        spec = self.build_spec(
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

    def _check_kind_validity(self, executable: str) -> None:
        """
        Check kind validity.

        Parameters
        ----------
        executable : str
            Executable string.
        """
        exec_kind = executable.split("://")[0]
        if self.EXECUTABLE_KIND != exec_kind:
            raise EntityError(f"Invalid task '{self.ENTITY_KIND}' for executable kind '{exec_kind}'")
