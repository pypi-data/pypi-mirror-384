# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod

from digitalhub.entities._base._base.entity import Base

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status


class Entity(Base):
    """
    Abstract class for entities.

    An entity is a collection of metadata, specifications.and status
    representing a variety of objects handled by Digitalhub.
    """

    # Entity type
    # Need to be set in subclasses
    ENTITY_TYPE: str

    # Attributes to render as dict. Need to be expanded in subclasses.
    _obj_attr = ["kind", "metadata", "spec", "status", "user", "key"]

    def __init__(
        self,
        kind: str,
        metadata: Metadata,
        spec: Spec,
        status: Status,
        user: str | None = None,
    ) -> None:
        self.kind = kind
        self.metadata = metadata
        self.spec = spec
        self.status = status
        self.user = user

        # Need to be set in subclasses
        self.key: str

    @abstractmethod
    def save(self, update: bool = False) -> Entity:
        """
        Abstract save method.
        """

    @abstractmethod
    def refresh(self) -> Entity:
        """
        Abstract refresh method.
        """

    def _update_attributes(self, obj: Entity) -> None:
        """
        Update attributes.

        Parameters
        ----------
        obj : dict
            Mapping representation of object.
        """
        self.metadata = obj.metadata
        self.spec = obj.spec
        self.status = obj.status
        self.user = obj.user

    @abstractmethod
    def export(self) -> str:
        """
        Abstract export method.
        """

    def add_relationship(self, relation: str, dest: str, source: str | None = None) -> None:
        """
        Add relationship to entity metadata.

        Parameters
        ----------
        relation : str
            The type of relationship.
        dest : str
            The target entity.
        source : str
            The source entity.
        """
        if self.metadata.relationships is None:
            self.metadata.relationships = []
        obj = {"type": relation, "dest": dest}
        if source is not None:
            obj["source"] = source
        self.metadata.relationships.append(obj)

    def to_dict(self) -> dict:
        """
        Override default to_dict method to add the possibility to exclude
        some attributes. This requires to set a list of _obj_attr
        attributes in the subclass.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        return {k: v for k, v in super().to_dict().items() if k in self._obj_attr}

    def __repr__(self) -> str:
        """
        Return string representation of the entity object.

        Returns
        -------
        str
            A string representing the entity instance.
        """
        return str(self.to_dict())
