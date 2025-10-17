# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import State
from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.status import Status


def build_status(status_cls: Status, **kwargs) -> Status:
    """
    Build entity status object. This method is used to build entity
    status.

    Parameters
    ----------
    status_cls : Status
        Entity status class.
    **kwargs : dict
        Keyword arguments.

    Returns
    -------
    Status
        Entity status object.
    """
    kwargs = parse_arguments(**kwargs)
    return status_cls(**kwargs)


def parse_arguments(**kwargs) -> dict:
    """
    Parse keyword arguments and add default values if necessary.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments.

    Returns
    -------
    dict
        Keyword arguments with default values.
    """
    state = kwargs.get("state")
    if state is None:
        kwargs["state"] = State.CREATED.value
    else:
        if kwargs["state"] not in State.__members__:
            raise BuilderError(f"Invalid state: {state}")
    return kwargs
