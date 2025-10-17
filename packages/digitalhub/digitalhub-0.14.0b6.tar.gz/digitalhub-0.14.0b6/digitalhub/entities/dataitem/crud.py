# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import context_processor
from digitalhub.entities.dataitem.utils import clean_tmp_path, eval_data, eval_source, post_process, process_kwargs
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem


ENTITY_TYPE = EntityTypes.DATAITEM.value


def new_dataitem(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    path: str | None = None,
    **kwargs,
) -> Dataitem:
    """
    Create a new object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    uuid : str
        ID of the object.
    description : str
        Description of the object (human readable).
    labels : list[str]
        List of labels.
    embedded : bool
        Flag to determine if object spec must be embedded in project spec.
    path : str
        Object path on local file system or remote storage. It is also the destination path of upload() method.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = new_dataitem(project="my-project",
    >>>                    name="my-dataitem",
    >>>                    kind="dataitem",
    >>>                    path="s3://my-bucket/my-key")
    """
    return context_processor.create_context_entity(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        path=path,
        **kwargs,
    )


def log_dataitem(
    project: str,
    name: str,
    kind: str,
    source: SourcesOrListOfSources | None = None,
    data: Any | None = None,
    path: str | None = None,
    file_format: str | None = None,
    read_df_params: dict | None = None,
    engine: str | None = "pandas",
    **kwargs,
) -> Dataitem:
    """
    Log a dataitem to the project.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    source : SourcesOrListOfSources
        Dataitem location on local path.
    data : Any
        Dataframe to log. Alternative to source.
    path : str
        Destination path of the dataitem. If not provided, it's generated.
    file_format : str
        Extension of the file source (parquet, csv, json, xlsx, txt).
    read_df_params : dict
        Parameters to pass to the dataframe reader.
    engine : str
        Dataframe engine (pandas, polars, etc.).
    **kwargs : dict
        New dataitem spec parameters.

    Returns
    -------
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = log_dataitem(project="my-project",
    >>>                    name="my-dataitem",
    >>>                    kind="table",
    >>>                    data=df)
    """
    cleanup = False
    if data is not None:
        cleanup = True

    source = eval_source(source, data, kind, name, project)
    data = eval_data(kind, source, data, file_format, read_df_params, engine)
    kwargs = process_kwargs(
        project,
        name,
        kind,
        source=source,
        data=data,
        path=path,
        **kwargs,
    )
    obj = context_processor.log_material_entity(
        source=source,
        project=project,
        name=name,
        kind=kind,
        **kwargs,
    )
    obj = post_process(obj, data)
    if cleanup:
        clean_tmp_path(source)
    return obj


def get_dataitem(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> Dataitem:
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
    Dataitem
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_dataitem("store://my-dataitem-key")

    Using entity name:
    >>> obj = get_dataitem("my-dataitem-name"
    >>>                    project="my-project",
    >>>                    entity_id="my-dataitem-id")
    """
    return context_processor.read_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
    )


def get_dataitem_versions(
    identifier: str,
    project: str | None = None,
) -> list[Dataitem]:
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
    list[Dataitem]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> objs = get_dataitem_versions("store://my-dataitem-key")

    Using entity name:
    >>> objs = get_dataitem_versions("my-dataitem-name",
    >>>                              project="my-project")
    """
    return context_processor.read_context_entity_versions(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
    )


def list_dataitems(
    project: str,
    q: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    user: str | None = None,
    state: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    version: str | None = None,
) -> list[Dataitem]:
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
    version : str
        Object version, default is latest.

    Returns
    -------
    list[Dataitem]
        List of object instances.

    Examples
    --------
    >>> objs = list_dataitems(project="my-project")
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
        version=version,
    )


def import_dataitem(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Dataitem:
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
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = import_dataitem("my-dataitem.yaml")
    """
    return context_processor.import_context_entity(
        file,
        key,
        reset_id,
        context,
    )


def load_dataitem(file: str) -> Dataitem:
    """
    Load object from a YAML file and update an existing object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = load_dataitem("my-dataitem.yaml")
    """
    return context_processor.load_context_entity(file)


def update_dataitem(entity: Dataitem) -> Dataitem:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Dataitem
        Object to update.

    Returns
    -------
    Dataitem
        Entity updated.

    Examples
    --------
    >>> obj = update_dataitem(obj)
    """
    return context_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_dataitem(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
    **kwargs,
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
    If delete_all_versions is False:
    >>> obj = delete_dataitem("store://my-dataitem-key")

    Otherwise:
    >>> obj = delete_dataitem("my-dataitem-name",
    >>>                       project="my-project",
    >>>                       delete_all_versions=True)
    """
    return context_processor.delete_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
        **kwargs,
    )
