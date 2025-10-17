# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.utils.generic_utils import dump_json


class Base:
    """
    Base class for all entities.
    It implements to_dict abd to_json method to represent
    the object as a dictionary/json and an any_setter method to
    set generic attributes coming from a constructor.
    """

    def to_dict(self) -> dict:
        """
        Return object as dict with all non private keys.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        obj = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_") and value is not None:
                if hasattr(value, "to_dict"):
                    sub_dict = value.to_dict()
                    if sub_dict:
                        obj[key] = sub_dict
                else:
                    obj[key] = value
        return obj

    def to_json(self) -> str:
        """
        Return object as json with all non private keys.

        Returns
        -------
        str
            A json string containing the attributes of the entity instance.
        """
        return dump_json(self.to_dict())

    def _any_setter(self, **kwargs) -> None:
        """
        Set any attribute of the object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to be set as attributes.
        """
        for k, v in kwargs.items():
            if k not in self.__dict__:
                setattr(self, k, v)

    def __repr__(self) -> str:
        """
        Return string representation of the entity object.

        Returns
        -------
        str
            A string representing the entity instance.
        """
        return str(self.to_dict())
