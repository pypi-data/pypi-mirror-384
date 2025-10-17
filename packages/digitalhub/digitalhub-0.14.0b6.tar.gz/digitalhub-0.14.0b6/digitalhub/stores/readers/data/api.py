# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.stores.readers.data.factory import factory
from digitalhub.utils.exceptions import ReaderError

if typing.TYPE_CHECKING:
    from digitalhub.stores.readers.data._base.reader import DataframeReader


def get_reader_by_engine(engine: str | None = None) -> DataframeReader:
    """
    Get Dataframe reader.

    Parameters
    ----------
    engine : str
        Dataframe engine (pandas, polars, etc.).

    Returns
    -------
    DataframeReader
        Reader object.
    """
    if engine is None:
        engine = factory.get_default()
    try:
        return factory.build(engine=engine)
    except KeyError:
        engines = factory.list_supported_engines()
        msg = f"Unsupported dataframe engine: '{engine}'. Supported engines: {engines}"
        raise ReaderError(msg)


def get_reader_by_object(obj: Any) -> DataframeReader:
    """
    Get Dataframe reader by object.

    Parameters
    ----------
    obj : Any
        Object to get reader from.

    Returns
    -------
    DataframeReader
        Reader object.
    """
    try:
        obj_name = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
        return factory.build(dataframe=obj_name)
    except KeyError:
        types = factory.list_supported_dataframes()
        msg = f"Unsupported dataframe type: '{obj}'. Supported types: {types}"
        raise ReaderError(msg)


def get_supported_engines() -> list[str]:
    """
    Get supported engines.

    Returns
    -------
    list
        List of supported engines.
    """
    return factory.list_supported_engines()


def get_supported_dataframes() -> list[str]:
    """
    Get supported dataframes.

    Returns
    -------
    list
        List of supported dataframes.
    """
    return factory.list_supported_dataframes()
