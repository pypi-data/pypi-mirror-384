# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.api import get_context
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.utils import get_project_from_key, is_valid_key, parse_entity_key
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.stores.client.api import get_client
from digitalhub.utils.exceptions import ContextError, EntityError, EntityNotExistsError

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.stores.client._base.client import Client


def parse_identifier(
    identifier: str,
    project: str | None = None,
    entity_type: str | None = None,
    entity_kind: str | None = None,
    entity_id: str | None = None,
) -> tuple[str, str, str | None, str | None, str | None]:
    """
    Parse and validate entity identifier into its components.

    Processes an entity identifier that can be either a full entity key
    (store://) or a simple entity name. When using a simple name,
    additional parameters must be provided for proper identification.

    Parameters
    ----------
    identifier : str
        The entity identifier to parse. Can be either a full entity key
        (store://project/entity_type/kind/name:id) or a simple entity name.
    project : str
        The project name. Required when identifier is not a full key.
    entity_type : str
        The entity type. Required when identifier is not a full key.
    entity_kind : str
        The entity kind specification.
    entity_id : str
        The entity version identifier.

    Returns
    -------
    tuple[str, str, str | None, str | None, str | None]
        A tuple containing (project_name, entity_type, entity_kind,
        entity_name, entity_id) parsed from the identifier.

    Raises
    ------
    ValueError
        If identifier is not a full key and project or entity_type is None.
    """
    if not is_valid_key(identifier):
        if project is None or entity_type is None:
            raise ValueError("Project and entity type must be specified.")
        return project, entity_type, entity_kind, identifier, entity_id
    return parse_entity_key(identifier)


def get_context_from_identifier(
    identifier: str,
    project: str | None = None,
) -> Context:
    """
    Retrieve context instance from entity identifier or project name.

    Extracts project information from the identifier and returns the
    corresponding context. If the identifier is not a full key, the
    project parameter must be provided explicitly.

    Parameters
    ----------
    identifier : str
        The entity identifier to extract context from. Can be either
        a full entity key (store://...) or a simple entity name.
    project : str
        The project name. Required when identifier is not a full key.

    Returns
    -------
    Context
        The context instance associated with the identified project.

    Raises
    ------
    EntityError
        If identifier is not a full key and project parameter is None.
    """
    if not is_valid_key(identifier):
        if project is None:
            raise EntityError("Specify project if you do not specify entity key.")
    else:
        project = get_project_from_key(identifier)

    return get_context_from_project(project)


def get_context_from_project(
    project: str,
) -> Context:
    """
    Retrieve context for a project, fetching from remote if necessary.

    Attempts to get the project context from the local cache first.
    If the project is not found locally, tries to fetch it from the
    remote backend and create the context.

    Parameters
    ----------
    project : str
        The name of the project to get context for.

    Returns
    -------
    Context
        The context instance for the specified project.

    Raises
    ------
    ContextError
        If the project cannot be found locally or remotely.
    """
    try:
        return get_context(project)
    except ContextError:
        return get_context_from_remote(project)


def get_context_from_remote(
    project: str,
) -> Context:
    """
    Fetch project context from remote backend and create local context.

    Retrieves project information from the remote backend, builds the
    project entity locally, and returns the corresponding context.
    Used when a project is not available in the local context cache.

    Parameters
    ----------
    project : str
        The name of the project to fetch from remote.

    Returns
    -------
    Context
        The context instance created from the remote project data.

    Raises
    ------
    ContextError
        If the project is not found on the remote backend.
    """
    try:
        client = get_client()
        obj = _read_base_entity(client, EntityTypes.PROJECT.value, project)
        entity_factory.build_entity_from_dict(obj)
        return get_context(project)
    except EntityNotExistsError:
        raise ContextError(f"Project '{project}' not found.")


def _read_base_entity(
    client: Client,
    entity_type: str,
    entity_name: str,
    **kwargs,
) -> dict:
    """
    Read entity data from the backend API.

    Internal utility function that performs a base-level entity read
    operation through the client API. Builds the appropriate API
    endpoint and retrieves the entity data as a dictionary.

    Parameters
    ----------
    client : Client
        The client instance to use for the API request.
    entity_type : str
        The type of entity to read (e.g., 'project', 'function').
    entity_name : str
        The name identifier of the entity to retrieve.
    **kwargs : dict
        Additional parameters to pass to the API call, such as
        version specifications or query filters.

    Returns
    -------
    dict
        Dictionary containing the entity data retrieved from the backend.
    """
    api = client.build_api(
        ApiCategories.BASE.value,
        BackendOperations.READ.value,
        entity_type=entity_type,
        entity_name=entity_name,
    )
    return client.read_object(api, **kwargs)
