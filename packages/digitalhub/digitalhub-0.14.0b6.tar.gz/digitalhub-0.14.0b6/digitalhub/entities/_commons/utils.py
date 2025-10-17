# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from collections import namedtuple

from digitalhub.entities._commons.enums import EntityTypes

KindAction = namedtuple("KindAction", ["kind", "action"])


KEY_PATTERN_WITH_ID = "store://([^/]+)/([^/]+)/([^/]+)/([^:]+):(.+)"
KEY_PATTERN_NO_ID = "store://([^/]+)/([^/]+)/([^/]+)/([^:]+)"


def is_valid_key(key: str) -> bool:
    """
    Check if an entity key is valid.

    Parameters
    ----------
    key : str
        The entity key to validate.

    Returns
    -------
    bool
        True if the key is valid, False otherwise.
    """
    return bool(re.fullmatch(KEY_PATTERN_WITH_ID, key) or re.fullmatch(KEY_PATTERN_NO_ID, key))


def sanitize_unversioned_key(key: str) -> str:
    """
    Sanitize an unversioned entity key (from name:id to id).

    Parameters
    ----------
    key : str
        The unversioned entity key.

    Returns
    -------
    str
        The sanitized entity key with version.
    """
    splt = key.split("/")[2:]
    ent_id = splt[-1].split(":")[0]
    return "store://" + "/".join(splt[:-1] + [ent_id])


def parse_entity_key(key: str) -> tuple[str, str, str, str | None, str]:
    """
    Parse an entity key into its constituent components.

    Extracts project name, entity type, kind, name, and UUID from a
    standardized entity key format. Handles special cases for tasks
    and runs which don't have name components.

    Parameters
    ----------
    key : str
        The entity key in format "store://project/type/kind/name:uuid"
        or "store://project/type/kind/uuid" for tasks and runs.

    Returns
    -------
    tuple[str, str, str, str | None, str]
        A tuple containing (project, entity_type, kind, name, uuid).
        The name component is None for tasks and runs.

    Raises
    ------
    ValueError
        If the key format is invalid or cannot be parsed.
    """
    if not is_valid_key(key):
        raise ValueError("Invalid entity key format.")

    # Remove "store://" from the key
    key = key.replace("store://", "")

    # Split the key into parts
    parts = key.split("/")

    # The project is the first part
    project = parts[0]

    # The entity type is the second part
    entity_type = parts[1]

    # The kind is the third part
    kind = parts[2]

    # Tasks and runs have no name and uuid
    if entity_type in (EntityTypes.TASK.value, EntityTypes.RUN.value):
        name = None
        uuid = parts[3]

    # The name and uuid are separated by a colon in the last part
    else:
        name, uuid = parts[3].split(":")

    return project, entity_type, kind, name, uuid


def get_entity_type_from_key(key: str) -> str:
    """
    Extract the entity type from an entity key.

    Parses the entity key and returns only the entity type component,
    which indicates the kind of entity (artifact, function, run, etc.).

    Parameters
    ----------
    key : str
        The entity key in standardized format.

    Returns
    -------
    str
        The entity type extracted from the key.

    Raises
    ------
    ValueError
        If the key format is invalid or cannot be parsed.
    """
    _, entity_type, _, _, _ = parse_entity_key(key)
    return entity_type


def get_project_from_key(key: str) -> str:
    """
    Extract the project name from an entity key.

    Parses the entity key and returns only the project component,
    which identifies the project context the entity belongs to.

    Parameters
    ----------
    key : str
        The entity key in standardized format.

    Returns
    -------
    str
        The project name extracted from the key.

    Raises
    ------
    ValueError
        If the key format is invalid or cannot be parsed.
    """
    project, _, _, _, _ = parse_entity_key(key)
    return project


def map_actions(kind_action_list: list[tuple[str, str]]) -> list[KindAction]:
    """
    Build task actions as KindAction namedtuples.

    Parameters
    ----------
    kind_action_list : list[tuple[str, str]]
        List of kind-action couples.

    Returns
    -------
    list[KindAction]
        Returns the task actions as KindAction namedtuples.
    """
    return [KindAction(kind, action) for (kind, action) in kind_action_list]
