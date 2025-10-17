# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.api import get_context
from digitalhub.stores.credentials.handler import creds_handler
from digitalhub.stores.data.builder import store_builder
from digitalhub.stores.data.enums import StoreEnv

if typing.TYPE_CHECKING:
    from digitalhub.stores.data._base.store import Store


def get_default_store(project: str) -> str:
    """
    Returns the default store URI for a given project.

    Parameters
    ----------
    project : str
        The name of the project.

    Returns
    -------
    str
        The default store URI.

    Raises
    ------
    ValueError
        If no default store is found.
    """
    var = StoreEnv.DEFAULT_FILES_STORE.value

    context = get_context(project)
    store = context.config.get(var.lower().replace("dhcore_", ""))
    if store is not None:
        return store

    store = creds_handler.load_from_env([var]).get(var)
    if store is None:
        store = creds_handler.load_from_file([var]).get(var)

    if store is None or store == "":
        raise ValueError(
            "No default store found. "
            "Please set a default store "
            f"in your environment (e.g. export {var}=) "
            " in the .dhcore.ini file "
            "or set it in project config."
        )
    return store


def get_store(uri: str) -> Store:
    """
    Returns a store instance for the given URI.

    Parameters
    ----------
    uri : str
        The URI to parse.

    Returns
    -------
    Store
        The store instance corresponding to the URI.
    """
    return store_builder.get(uri)
