# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import uuid4

from digitalhub.utils.generic_utils import slugify_string


def build_uuid(uuid: str | None = None) -> str:
    """
    Create a uuid if not given. If given, validate it.

    Parameters
    ----------
    uuid : str
        ID of the object.

    Returns
    -------
    str
        Validated UUID4.
    """
    if uuid is not None:
        if slugify_string(uuid) != uuid:
            raise ValueError(f"Invalid ID: {uuid}. Must pass slugified ID.")
        return uuid
    return uuid4().hex
