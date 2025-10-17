# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import context_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


ENTITY_TYPE = EntityTypes.RUN.value


def new_run(
    project: str,
    kind: str,
    uuid: str | None = None,
    labels: list[str] | None = None,
    task: str | None = None,
    local_execution: bool = False,
    **kwargs,
) -> Run:
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
    task : str
        Name of the task associated with the run.
    local_execution : bool
        Flag to determine if object has local execution.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Run
        Object instance.

    Examples
    --------
    >>> obj = new_run(project="my-project",
    >>>               kind="python+run",
    >>>               task="task-string")
    """
    return context_processor.create_context_entity(
        project=project,
        kind=kind,
        uuid=uuid,
        labels=labels,
        task=task,
        local_execution=local_execution,
        **kwargs,
    )


def get_run(
    identifier: str,
    project: str | None = None,
) -> Run:
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
    Run
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_run("store://my-run-key")

    Using entity ID:
    >>> obj = get_run("my-run-id"
    >>>               project="my-project")
    """
    return context_processor.read_unversioned_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
    )


def list_runs(
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
    task: str | None = None,
    action: str | None = None,
) -> list[Run]:
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
    task : str
        Task string filter.
    action : str
        Action name filter.

    Returns
    -------
    list[Model]
        List of object instances.

    Examples
    --------
    >>> objs = list_runs(project="my-project")
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
        task=task,
        action=action,
    )


def import_run(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Run:
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
    Run
        Object instance.

    Example
    -------
    >>> obj = import_run("my-run.yaml")
    """
    return context_processor.import_context_entity(
        file,
        key,
        reset_id,
        context,
    )


def load_run(file: str) -> Run:
    """
    Load object from a YAML file and update an existing object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Run
        Object instance.

    Examples
    --------
    >>> obj = load_run("my-run.yaml")
    """
    return context_processor.load_context_entity(file)


def update_run(entity: Run) -> Run:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Run
        Object to update.

    Returns
    -------
    Run
        Entity updated.

    Examples
    --------
    >>> obj = update_run(obj)
    """
    return context_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_run(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
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

    Returns
    -------
    dict
        Response from backend.

    Examples
    --------
    >>> obj = delete_run("store://my-run-key")
    >>> obj = delete_run(
    ...     "my-run-id",
    ...     project="my-project",
    ... )
    """
    return context_processor.delete_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
    )
