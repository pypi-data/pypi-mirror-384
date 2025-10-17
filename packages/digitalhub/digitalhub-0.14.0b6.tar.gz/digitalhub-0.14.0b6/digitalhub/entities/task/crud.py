# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import context_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.task._base.entity import Task


ENTITY_TYPE = EntityTypes.TASK.value


def new_task(
    project: str,
    kind: str,
    uuid: str | None = None,
    labels: list[str] | None = None,
    function: str | None = None,
    workflow: str | None = None,
    **kwargs,
) -> Task:
    """
    Create a new object.

    Parameters
    ----------
    project : str
        Project name.
    kind : str
        Kind the object.
    uuid : str
        ID of the object.
    labels : list[str]
        List of labels.
    function : str
        Name of the executable associated with the task.
    workflow : str
        Name of the workflow associated with the task.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Task
        Object instance.

    Examples
    --------
    >>> obj = new_task(project="my-project",
    >>>                kind="python+job",
    >>>                function="function-string")
    """
    return context_processor.create_context_entity(
        project=project,
        kind=kind,
        uuid=uuid,
        labels=labels,
        function=function,
        workflow=workflow,
        **kwargs,
    )


def get_task(
    identifier: str,
    project: str | None = None,
) -> Task:
    """
    Get object from backend.

    Parameters
    ----------
    identifier : str
        Entity key (store://...) or entity ID.
    project : str
        Project name.

    Returns
    -------
    Task
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_task("store://my-task-key")

    Using entity ID:
    >>> obj = get_task("my-task-id"
    >>>               project="my-project")
    """
    return context_processor.read_unversioned_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
    )


def list_tasks(
    project: str,
    q: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    user: str | None = None,
    state: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    function: str | None = None,
    workflow: str | None = None,
) -> list[Task]:
    """
    List all latest version objects from backend.

    Parameters
    ----------
    project : str
        Project name.
    q : str
        Query string to filter objects.
    name : str
        Object name.
    kind : str
        Kind of the object.
    user : str
        User that created the object.
    state : str
        Object state.
    created : str
        Creation date filter.
    updated : str
        Update date filter.
    function : str
        Function key filter.
    workflow : str
        Workflow key filter.

    Returns
    -------
    list[Task]
        List of object instances.

    Examples
    --------
    >>> objs = list_tasks(project="my-project")
    """
    return context_processor.list_context_entities(
        project=project,
        entity_type=ENTITY_TYPE,
        q=q,
        name=name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated,
        function=function,
        workflow=workflow,
    )


def import_task(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Task:
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
    Task
        Object instance.

    Example
    -------
    >>> obj = import_task("my-task.yaml")
    """
    return context_processor.import_context_entity(
        file,
        key,
        reset_id,
        context,
    )


def load_task(file: str) -> Task:
    """
    Load object from a YAML file and update an existing object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Task
        Object instance.

    Examples
    --------
    >>> obj = load_task("my-task.yaml")
    """
    return context_processor.load_context_entity(file)


def update_task(entity: Task) -> Task:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Task
        Object to update.

    Returns
    -------
    Task
        Entity updated.

    Examples
    --------
    >>> obj = update_task(obj)
    """
    return context_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_task(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    cascade: bool = True,
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
    cascade : bool
        Cascade delete.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    dict
        Response from backend.

    Examples
    --------
    >>> obj = delete_task("store://my-task-key")
    """
    return context_processor.delete_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        cascade=cascade,
    )
