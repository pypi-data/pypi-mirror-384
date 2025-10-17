# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
import typing
from typing import Any

from digitalhub.context.api import get_context
from digitalhub.entities._base.material.utils import build_log_path_from_source, eval_local_source
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.stores.data.api import get_store
from digitalhub.stores.readers.data.api import get_reader_by_object
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.generic_utils import slugify_string
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem


DEFAULT_EXTENSION = FileExtensions.PARQUET.value


def eval_source(
    source: SourcesOrListOfSources | None = None,
    data: Any | None = None,
    kind: str | None = None,
    name: str | None = None,
    project: str | None = None,
) -> Any:
    """
    Evaluate and process data source for dataitem creation.

    Determines the appropriate source handling based on whether a source
    path or data object is provided. For table dataitems with data objects,
    writes the data to a Parquet file and returns the file path.

    Parameters
    ----------
    source : SourcesOrListOfSources
        The source specification(s) for the dataitem. Can be file paths,
        URLs, or other source identifiers.
    data : Any
        The data object to process (e.g., DataFrame). Alternative to source.
        Exactly one of source or data must be provided.
    kind : str
        The kind of dataitem being created (e.g., 'table').
    name : str
        The name of the dataitem, used for generating file paths.
    project : str
        The project name, used for context and path generation.

    Returns
    -------
    Any
        The processed source. Returns the original source if provided,
        or the path to a generated file if data was processed.

    Raises
    ------
    ValueError
        If both source and data are provided or both are None.
    NotImplementedError
        If the specified kind is not supported for data processing.
    """
    if (source is None) == (data is None):
        raise ValueError("You must provide source or data.")

    if source is not None:
        eval_local_source(source)
        return source

    if kind == EntityKinds.DATAITEM_TABLE.value:
        ctx = get_context(project)
        pth = ctx.root / f"{slugify_string(name)}.{DEFAULT_EXTENSION}"
        reader = get_reader_by_object(data)
        reader.write_parquet(data, pth)
        return str(pth)

    raise NotImplementedError


def eval_data(
    kind: str,
    source: SourcesOrListOfSources,
    data: Any | None = None,
    file_format: str | None = None,
    read_df_params: dict | None = None,
    engine: str | None = None,
) -> Any:
    """
    Evaluate and load data from source or return provided data.

    For table dataitems, loads data from the source using the appropriate
    store and reader. For other kinds, returns the data as-is.

    Parameters
    ----------
    kind : str
        The kind of dataitem (e.g., 'table') that determines
        how data should be processed.
    source : SourcesOrListOfSources
        The source specification(s) to load data from.
    data : Any
        Pre-loaded data object. If provided, may be returned directly
        depending on the dataitem kind.
    file_format : str
        The file format specification for reading the source
        (e.g., 'parquet', 'csv').
    engine : str
        The engine to use for reading the data (e.g., 'pandas', 'polars').

    Returns
    -------
    Any
        The loaded data object for table dataitems, or the original
        data parameter for other kinds.
    """
    if kind == EntityKinds.DATAITEM_TABLE.value:
        if data is None:
            if read_df_params is None:
                read_df_params = {}
            return get_store(source).read_df(
                source,
                file_format=file_format,
                engine=engine,
                **read_df_params,
            )
    return data


def process_kwargs(
    project: str,
    name: str,
    kind: str,
    source: SourcesOrListOfSources,
    data: Any | None = None,
    path: str | None = None,
    **kwargs,
) -> dict:
    """
    Process and enhance specification parameters for dataitem creation.

    Processes the keyword arguments for dataitem specification, handling
    schema extraction for table dataitems and path generation. Extracts
    schema information from data objects when available.

    Parameters
    ----------
    project : str
        The name of the project.
    name : str
        The name of the dataitem entity.
    kind : str
        The kind of dataitem being created (e.g., 'table').
    source : SourcesOrListOfSources
        The source specification(s) for the dataitem content.
    data : Any
        The data object for schema extraction and processing.
        Used as an alternative to source for table dataitems.
    path : str
        The destination path for the dataitem entity.
        If None, a path will be automatically generated.
    **kwargs : dict
        Additional specification parameters to be processed
        and passed to the dataitem creation.

    Returns
    -------
    dict
        The updated kwargs dictionary with processed path,
        UUID, and schema information included.
    """
    if data is not None:
        if kind == EntityKinds.DATAITEM_TABLE.value:
            reader = get_reader_by_object(data)
            kwargs["schema"] = reader.get_schema(data)
    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        kwargs["path"] = build_log_path_from_source(project, EntityTypes.DATAITEM.value, name, uuid, source)
    else:
        kwargs["path"] = path
    return kwargs


def clean_tmp_path(pth: SourcesOrListOfSources) -> None:
    """
    Clean up temporary files and directories.

    Removes temporary files or directories created during dataitem
    processing. Handles both single paths and lists of paths,
    ignoring any errors that occur during cleanup.

    Parameters
    ----------
    pth : SourcesOrListOfSources
        The path or list of paths to clean up. Can be file paths
        or directory paths that need to be removed.
    """
    if isinstance(pth, list):
        for p in pth:
            shutil.rmtree(p, ignore_errors=True)
        return
    shutil.rmtree(pth, ignore_errors=True)


def post_process(obj: Dataitem, data: Any) -> Dataitem:
    """
    Post-process dataitem object with additional metadata and previews.

    Enhances the dataitem object with additional information extracted
    from the data. For table dataitems, generates and stores a data
    preview in the object's status.

    Parameters
    ----------
    obj : Dataitem
        The dataitem object to post-process and enhance.
    data : Any
        The data object used to generate previews and extract
        additional metadata information.

    Returns
    -------
    Dataitem
        The enhanced dataitem object with updated status information
        and saved changes.
    """
    if obj.kind == EntityKinds.DATAITEM_TABLE.value:
        reader = get_reader_by_object(data)
        obj.status.preview = reader.get_preview(data)
        obj.save(update=True)
    return obj
