# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod

from digitalhub.entities._constructors.metadata import build_metadata
from digitalhub.entities._constructors.name import build_name
from digitalhub.entities._constructors.spec import build_spec
from digitalhub.entities._constructors.status import build_status
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.entity import Entity
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities._base.entity.spec import Spec, SpecValidator
    from digitalhub.entities._base.entity.status import Status


class EntityBuilder:
    """
    Builder class for building entities.
    """

    # Class variables
    ENTITY_TYPE: str = None
    ENTITY_CLASS: type[Entity] = None
    ENTITY_SPEC_CLASS: type[Spec] = None
    ENTITY_SPEC_VALIDATOR: type[SpecValidator] = None
    ENTITY_STATUS_CLASS: type[Status] = None
    ENTITY_KIND: str = None

    def __init__(self) -> None:
        if self.ENTITY_TYPE is None:
            raise BuilderError("ENTITY_TYPE must be set")
        if self.ENTITY_CLASS is None:
            raise BuilderError("ENTITY_CLASS must be set")
        if self.ENTITY_SPEC_CLASS is None:
            raise BuilderError("ENTITY_SPEC_CLASS must be set")
        if self.ENTITY_SPEC_VALIDATOR is None:
            raise BuilderError("ENTITY_SPEC_VALIDATOR must be set")
        if self.ENTITY_STATUS_CLASS is None:
            raise BuilderError("ENTITY_STATUS_CLASS must be set")
        if self.ENTITY_KIND is None:
            raise BuilderError("ENTITY_KIND must be set")

    def build_name(self, name: str) -> str:
        """
        Build entity name.

        Parameters
        ----------
        name : str
            Entity name.

        Returns
        -------
        str
            Entity name.
        """
        return build_name(name)

    def build_uuid(self, uuid: str | None = None) -> str:
        """
        Build entity uuid.

        Parameters
        ----------
        uuid : str
            Entity uuid.

        Returns
        -------
        str
            Entity uuid.
        """
        return build_uuid(uuid)

    def build_metadata(self, **kwargs) -> Metadata:
        """
        Build entity metadata object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments for the constructor.

        Returns
        -------
        Metadata
            Metadata object.
        """
        return build_metadata(**kwargs)

    def build_spec(self, validate: bool = True, **kwargs) -> Spec:
        """
        Build entity spec object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments for the constructor.

        Returns
        -------
        Spec
            Spec object.
        """
        return build_spec(
            self.ENTITY_SPEC_CLASS,
            self.ENTITY_SPEC_VALIDATOR,
            validate=validate,
            **kwargs,
        )

    def build_status(self, **kwargs) -> Status:
        """
        Build entity status object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments for the constructor.

        Returns
        -------
        Status
            Status object.
        """
        return build_status(self.ENTITY_STATUS_CLASS, **kwargs)

    def build_entity(self, **kwargs) -> Entity:
        """
        Build entity object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments for the constructor.

        Returns
        -------
        Entity
            Entity object.
        """
        return self.ENTITY_CLASS(**kwargs)

    @abstractmethod
    def build(self, *args, **kwargs) -> Entity:
        """
        Build entity object.
        """

    @abstractmethod
    def from_dict(self, obj: dict, validate: bool = True) -> Entity:
        """
        Build entity object from dictionary.
        """

    def get_entity_type(self) -> str:
        """
        Get entity type.

        Returns
        -------
        str
            Entity type.
        """
        return self.ENTITY_TYPE

    def get_kind(self) -> str:
        """
        Get entity kind.

        Returns
        -------
        str
            Entity kind.
        """
        return self.ENTITY_KIND

    def get_spec_validator(self) -> type[SpecValidator]:
        """
        Get entity spec validator.

        Returns
        -------
        type[SpecValidator]
            Entity spec validator.
        """
        return self.ENTITY_SPEC_VALIDATOR
