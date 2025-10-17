# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.utils import is_valid_key
from digitalhub.entities._processors.processors import context_processor
from digitalhub.utils.exceptions import EntityNotExistsError

if typing.TYPE_CHECKING:
    from digitalhub.entities.secret._base.entity import Secret


ENTITY_TYPE = EntityTypes.SECRET.value


def new_secret(
    project: str,
    name: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    secret_value: str | None = None,
    **kwargs,
) -> Secret:
    """
    Create a new object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    uuid : str
        ID of the object.
    description : str
        Description of the object (human readable).
    labels : list[str]
        List of labels.
    embedded : bool
        Flag to determine if object spec must be embedded in project spec.
    secret_value : str
        Value of the secret.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Secret
        Object instance.

    Examples
    --------
    >>> obj = new_secret(project="my-project",
    >>>                  name="my-secret",
    >>>                  secret_value="my-secret-value")
    """
    if secret_value is None:
        raise ValueError("secret_value must be provided.")
    obj: Secret = context_processor.create_context_entity(
        project=project,
        name=name,
        kind="secret",
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        **kwargs,
    )
    obj.set_secret_value(value=secret_value)
    return obj


def get_secret(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> Secret:
    """
    Get object from backend.

    Parameters
    ----------
    identifier : str
        Entity key (store://...) or entity name.
    project : str
        Project name.
    entity_id : str
        Entity ID.

    Returns
    -------
    Secret
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_secret("store://my-secret-key")

    Using entity name:
    >>> obj = get_secret("my-secret-name"
    >>>                  project="my-project",
    >>>                  entity_id="my-secret-id")
    """
    if not is_valid_key(identifier):
        if project is None:
            raise ValueError("Project must be provided.")
        secrets = list_secrets(project=project)
        for secret in secrets:
            if secret.name == identifier:
                return secret
        else:
            raise EntityNotExistsError(f"Secret {identifier} not found.")
    return context_processor.read_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
    )


def get_secret_versions(
    identifier: str,
    project: str | None = None,
) -> list[Secret]:
    """
    Get object versions from backend.

    Parameters
    ----------
    identifier : str
        Entity key (store://...) or entity name.
    project : str
        Project name.

    Returns
    -------
    list[Secret]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> objs = get_secret_versions("store://my-secret-key")

    Using entity name:
    >>> objs = get_secret_versions("my-secret-name",
    >>>                            project="my-project")
    """
    return context_processor.read_context_entity_versions(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
    )


def list_secrets(project: str) -> list[Secret]:
    """
    List all latest version objects from backend.

    Parameters
    ----------
    project : str
        Project name.

    Returns
    -------
    list[Secret]
        List of object instances.

    Examples
    --------
    >>> objs = list_secrets(project="my-project")
    """
    return context_processor.list_context_entities(
        project=project,
        entity_type=ENTITY_TYPE,
    )


def import_secret(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Secret:
    """
    Import an object from a YAML file or from a storage key.

    Parameters
    ----------
    file : str
        Path to the YAML file.
    key : str
        Entity key (store://...).
    reset_id : bool
        Flag to determine if the ID of executable entities should be reset.
    context : str
        Project name to use for context resolution.

    Returns
    -------
    Secret
        Object instance.

    Examples
    --------
    >>> obj = import_secret("my-secret.yaml")
    """
    return context_processor.import_context_entity(
        file,
        key,
        reset_id,
        context,
    )


def load_secret(file: str) -> Secret:
    """
    Load object from a YAML file and update an existing object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Secret
        Object instance.

    Examples
    --------
    >>> obj = load_secret("my-secret.yaml")
    """
    return context_processor.load_context_entity(file)


def update_secret(entity: Secret) -> Secret:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Secret
        Object to update.

    Returns
    -------
    Secret
        Entity updated.

    Examples
    --------
    >>> obj = update_secret(obj)
    """
    return context_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_secret(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
) -> dict:
    """
    Delete object from backend.

    Parameters
    ----------
    identifier : str
        Entity key (store://...) or entity name.
    project : str
        Project name.
    entity_id : str
        Entity ID.
    delete_all_versions : bool
        Delete all versions of the named entity.
        If True, use entity name instead of entity key as identifier.

    Returns
    -------
    dict
        Response from backend.

    Examples
    --------
    If delete_all_versions is False:
    >>> obj = delete_secret("store://my-secret-key")

    Otherwise:
    >>> obj = delete_secret("my-secret-name"
    >>>                     project="my-project",
    >>>                     delete_all_versions=True)
    """
    return context_processor.delete_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
    )
