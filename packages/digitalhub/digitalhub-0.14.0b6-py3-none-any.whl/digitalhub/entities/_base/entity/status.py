# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base._base.entity import Base


class Status(Base):
    """
    Base Status class.
    The status class contains information about the state of an entity,
    for example, the state of a RUNNING run, and eventual error message.
    """

    def __init__(
        self,
        state: str,
        message: str | None = None,
        transitions: list[dict] | None = None,
        k8s: dict | None = None,
        **kwargs,
    ) -> None:
        self.state = state
        self.message = message
        self.transitions = transitions
        self.k8s = k8s

        self._any_setter(**kwargs)

    @classmethod
    def from_dict(cls, obj: dict) -> Status:
        """
        Return entity status object from dictionary.

        Parameters
        ----------
        obj : dict
            A dictionary containing the attributes of the entity status.

        Returns
        -------
        EntityStatus
            An entity status object.
        """
        return cls(**obj)
