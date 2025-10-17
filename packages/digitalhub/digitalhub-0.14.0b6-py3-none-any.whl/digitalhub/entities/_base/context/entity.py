# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.api import get_context
from digitalhub.entities._base.entity.entity import Entity
from digitalhub.entities._processors.processors import context_processor
from digitalhub.utils.generic_utils import get_timestamp
from digitalhub.utils.io_utils import write_yaml

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status


class ContextEntity(Entity):
    def __init__(
        self,
        project: str,
        kind: str,
        metadata: Metadata,
        spec: Spec,
        status: Status,
        user: str | None = None,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)
        self.project = project
        self.name: str
        self.id: str

        # Different behaviour for versioned and unversioned
        self._obj_attr.extend(["project", "id", "name"])

    ##############################
    #  Save / Refresh / Export
    ##############################

    def save(self, update: bool = False) -> ContextEntity:
        """
        Save or update the entity into the backend.

        Parameters
        ----------
        update : bool
            Flag to indicate update.

        Returns
        -------
        ContextEntity
            Entity saved.
        """
        if update:
            return self._update()
        return self._save()

    def _save(self) -> ContextEntity:
        """
        Save entity into backend.

        Returns
        -------
        ContextEntity
            Entity saved.
        """
        new_obj = context_processor.create_context_entity(_entity=self)
        self._update_attributes(new_obj)
        return self

    def _update(self) -> ContextEntity:
        """
        Update entity in backend.

        Returns
        -------
        ContextEntity
            Entity updated.
        """
        if self._context().local:
            self.metadata.updated = self.metadata.updated = get_timestamp()
        new_obj = context_processor.update_context_entity(self.project, self.ENTITY_TYPE, self.id, self.to_dict())
        self._update_attributes(new_obj)
        return self

    def export(self) -> str:
        """
        Export object as a YAML file in the context folder.

        Returns
        -------
        str
            Exported filepath.
        """
        obj = self.to_dict()
        pth = self._context().root / f"{self.ENTITY_TYPE}s-{self.id}.yaml"
        write_yaml(pth, obj)
        return str(pth)

    def refresh(self) -> ContextEntity:
        """
        Refresh object from backend.

        Returns
        -------
        ContextEntity
            Entity refreshed.
        """
        new_obj = context_processor.read_context_entity(self.key)
        self._update_attributes(new_obj)
        return self

    ##############################
    #  Context
    ##############################

    def _context(self) -> Context:
        """
        Get context.

        Returns
        -------
        Context
            Context object.
        """
        return get_context(self.project)
