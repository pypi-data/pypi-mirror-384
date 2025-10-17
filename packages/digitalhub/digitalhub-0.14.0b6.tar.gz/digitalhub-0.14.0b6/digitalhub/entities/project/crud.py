# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import base_processor, context_processor
from digitalhub.entities.project.utils import setup_project
from digitalhub.utils.exceptions import BackendError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities.project._base.entity import Project


ENTITY_TYPE = EntityTypes.PROJECT.value


def new_project(
    name: str,
    description: str | None = None,
    labels: list[str] | None = None,
    local: bool = False,
    config: dict | None = None,
    context: str | None = None,
    setup_kwargs: dict | None = None,
    **kwargs,
) -> Project:
    """
    Create a new object.

    Parameters
    ----------
    name : str
        Object name.
    description : str
        Description of the object (human readable).
    labels : list[str]
        List of labels.
    local : bool
        If True, use local backend, if False use DHCore backend. Default to False.
    config : dict
        DHCore environment configuration.
    context : str
        The context local folder of the project.
    setup_kwargs : dict
        Setup keyword arguments passed to setup_project() function.
    **kwargs : dict
        Keyword arguments.

    Returns
    -------
    Project
        Object instance.

    Examples
    --------
    >>> obj = new_project("my-project")
    """
    if context is None:
        context = "./"
    obj = base_processor.create_project_entity(
        name=name,
        kind="project",
        description=description,
        labels=labels,
        local=local,
        config=config,
        context=context,
        **kwargs,
    )
    return setup_project(obj, setup_kwargs)


def get_project(
    name: str,
    local: bool = False,
    setup_kwargs: dict | None = None,
) -> Project:
    """
    Retrieves project details from backend.

    Parameters
    ----------
    name : str
        The Project name.
    local : bool
        Flag to determine if backend is local.
    setup_kwargs : dict
        Setup keyword arguments passed to setup_project() function.

    Returns
    -------
    Project
        Object instance.

    Examples
    --------
    >>> obj = get_project("my-project")
    """
    obj = base_processor.read_project_entity(
        entity_type=ENTITY_TYPE,
        entity_name=name,
        local=local,
    )
    return setup_project(obj, setup_kwargs)


def import_project(
    file: str,
    local: bool = False,
    setup_kwargs: dict | None = None,
    reset_id: bool = False,
) -> Project:
    """
    Import object from a YAML file and create a new object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.
    local : bool
        Flag to determine if backend is local.
    setup_kwargs : dict
        Setup keyword arguments passed to setup_project() function.
    reset_id : bool
        Flag to determine if the ID of project entities should be reset.

    Returns
    -------
    Project
        Object instance.

    Examples
    --------
    >>> obj = import_project("my-project.yaml")
    """
    obj = base_processor.import_project_entity(
        file=file,
        local=local,
        reset_id=reset_id,
    )
    return setup_project(obj, setup_kwargs)


def load_project(
    file: str,
    local: bool = False,
    setup_kwargs: dict | None = None,
) -> Project:
    """
    Load object from a YAML file and update an existing object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.
    local : bool
        Flag to determine if backend is local.
    setup_kwargs : dict
        Setup keyword arguments passed to setup_project() function.

    Returns
    -------
    Project
        Object instance.

    Examples
    --------
    >>> obj = load_project("my-project.yaml")
    """
    obj = base_processor.load_project_entity(file=file, local=local)
    return setup_project(obj, setup_kwargs)


def list_projects(local: bool = False) -> list[Project]:
    """
    List projects in backend.

    Parameters
    ----------
    local : bool
        Flag to determine if backend is local.

    Returns
    -------
    list
        List of objects.
    """
    return base_processor.list_project_entities(local=local)


def get_or_create_project(
    name: str,
    local: bool = False,
    config: dict | None = None,
    context: str | None = None,
    setup_kwargs: dict | None = None,
    **kwargs,
) -> Project:
    """
    Try to get project. If not exists, create it.

    Parameters
    ----------
    name : str
        Project name.
    local : bool
        Flag to determine if backend is local.
    config : dict
        DHCore environment configuration.
    context : str
        Folder where the project will saves its context locally.
    setup_kwargs : dict
        Setup keyword arguments passed to setup_project() function.
    **kwargs : dict
        Keyword arguments.

    Returns
    -------
    Project
        Object instance.
    """
    try:
        return get_project(
            name,
            local=local,
            setup_kwargs=setup_kwargs,
            **kwargs,
        )
    except BackendError:
        return new_project(
            name,
            local=local,
            config=config,
            setup_kwargs=setup_kwargs,
            context=context,
            **kwargs,
        )


def update_project(entity: Project, **kwargs) -> Project:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Project
        Object to update.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    Project
        The updated object.

    Examples
    --------
    >>> obj = update_project(obj)
    """
    return base_processor.update_project_entity(
        entity_type=entity.ENTITY_TYPE,
        entity_name=entity.name,
        entity_dict=entity.to_dict(),
        local=entity._client.is_local(),
        **kwargs,
    )


def delete_project(
    name: str,
    cascade: bool = True,
    clean_context: bool = True,
    local: bool = False,
) -> dict:
    """
    Delete a project.

    Parameters
    ----------
    name : str
        Project name.
    cascade : bool
        Flag to determine if delete is cascading.
    clean_context : bool
        Flag to determine if context will be deleted.
    local : bool
        Flag to determine if backend is local.

    Returns
    -------
    dict
        Response from backend.

    Examples
    --------
    >>> delete_project("my-project")
    """
    return base_processor.delete_project_entity(
        entity_type=ENTITY_TYPE,
        entity_name=name,
        local=local,
        cascade=cascade,
        clean_context=clean_context,
    )


def search_entity(
    project_name: str,
    query: str | None = None,
    entity_types: list[str] | None = None,
    name: str | None = None,
    kind: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
) -> list[ContextEntity]:
    """
    Search objects from backend.

    Parameters
    ----------
    project_name : str
        Project name.
    query : str
        Search query.
    entity_types : list[str]
        Entity types.
    name : str
        Entity name.
    kind : str
        Entity kind.
    created : str
        Entity creation date.
    updated : str
        Entity update date.
    description : str
        Entity description.
    labels : list[str]
        Entity labels.

    Returns
    -------
    list[ContextEntity]
        List of object instances.
    """
    return context_processor.search_entity(
        project_name,
        query=query,
        entity_types=entity_types,
        name=name,
        kind=kind,
        created=created,
        updated=updated,
        description=description,
        labels=labels,
    )
