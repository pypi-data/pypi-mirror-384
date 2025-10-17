# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import ValidationError

from digitalhub.entities._base.entity.metadata import Metadata, RelationshipValidator
from digitalhub.utils.exceptions import BuilderError
from digitalhub.utils.generic_utils import get_timestamp


def build_metadata(**kwargs) -> Metadata:
    """
    Build entity metadata object. This method is used to build entity
    metadata.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments for the constructor.

    Returns
    -------
    Metadata
        Metadata object.
    """
    kwargs = parse_arguments(**kwargs)
    return Metadata(**kwargs)


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
        A dictionary containing the entity metadata attributes.
    """
    if "created" not in kwargs or kwargs["created"] is None:
        kwargs["created"] = get_timestamp()
    if "updated" not in kwargs or kwargs["updated"] is None:
        kwargs["updated"] = kwargs["created"]
    if "relationships" in kwargs:
        if not isinstance(kwargs["relationships"], list):
            raise BuilderError("Invalid relationships format. Must be a list of maps.")
        for relationship in kwargs["relationships"]:
            try:
                RelationshipValidator(**relationship)
            except ValidationError as e:
                raise BuilderError(f"Malformed relationship: {e}") from e
    return kwargs
