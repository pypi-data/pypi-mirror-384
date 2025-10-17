# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from digitalhub.entities._base._base.entity import Base


class Spec(Base):
    """
    A class representing the specifications.of an entity.
    specifications.is a collection of information about an entity
    thought to be immutable by the user.
    """

    @classmethod
    def from_dict(cls, obj: dict) -> Spec:
        """
        Return entity specifications.object from dictionary.

        Parameters
        ----------
        obj : dict
            A dictionary containing the attributes of the entity specifications.

        Returns
        -------
        EntitySpec
            An entity specifications.object.
        """
        return cls(**obj)


class SpecValidator(BaseModel):
    """
    A class representing the parameters of an entity.
    This base class is used to define the parameters of an entity
    specifications.and is used to validate the parameters passed
    to the constructor.
    """

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)


class MaterialSpec(Spec):
    """
    Material specifications.class.
    """

    def __init__(self, path: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = path


class MaterialValidator(SpecValidator):
    """
    Material parameters class.
    """

    path: str
    """Target path to file(s)"""
