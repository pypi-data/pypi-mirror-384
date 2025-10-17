# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.data.local.store import LocalStore
from digitalhub.stores.data.remote.store import RemoteStore
from digitalhub.stores.data.s3.configurator import S3StoreConfigurator
from digitalhub.stores.data.s3.store import S3Store
from digitalhub.stores.data.sql.configurator import SqlStoreConfigurator
from digitalhub.stores.data.sql.store import SqlStore
from digitalhub.utils.uri_utils import SchemeCategory, map_uri_scheme

if typing.TYPE_CHECKING:
    from digitalhub.stores.credentials.configurator import Configurator
    from digitalhub.stores.data._base.store import Store
    from digitalhub.utils.exceptions import StoreError


class StoreInfo:
    """
    Container for store class and configurator information.

    Holds store class references and their associated configurators
    for registration and instantiation in the store builder system.

    Attributes
    ----------
    _store : Store
        The store class to be instantiated.
    _configurator : Configurator or None
        The configurator class for store configuration, if required.
    """

    def __init__(self, store: Store, configurator: Configurator | None = None) -> None:
        self._store = store
        self._configurator = configurator


class StoreBuilder:
    """
    Store factory and registry for managing data store instances.

    Provides registration, instantiation, and caching of data store
    instances based on URI schemes. Supports various store types
    including S3, SQL, local, and remote stores with their respective
    configurators.

    Attributes
    ----------
    _builders : dict[str, StoreInfo]
        Registry of store types mapped to their StoreInfo instances.
    _instances : dict[str, Store]
        Cache of instantiated store instances by store type.
    """

    def __init__(self) -> None:
        self._builders: dict[str, StoreInfo] = {}
        self._instances: dict[str, dict[str, Store]] = {}

    def register(
        self,
        store_type: str,
        store: Store,
        configurator: Configurator | None = None,
    ) -> None:
        """
        Register a store type with its class and optional configurator.

        Adds a new store type to the builder registry, associating it
        with a store class and optional configurator for later instantiation.

        Parameters
        ----------
        store_type : str
            The unique identifier for the store type (e.g., 's3', 'sql').
        store : Store
            The store class to register for this type.
        configurator : Configurator
            The configurator class for store configuration.
            If None, the store will be instantiated without configuration.

        Raises
        ------
        StoreError
            If the store type is already registered in the builder.
        """
        if store_type not in self._builders:
            self._builders[store_type] = StoreInfo(store, configurator)
        else:
            raise StoreError(f"Store type {store_type} already registered")

    def get(self, uri: str) -> Store:
        """
        Get or create a store instance based on URI scheme.

        Determines the appropriate store type from the URI scheme,
        instantiates the store if not already cached, and returns
        the store instance. Store instances are cached for reuse.

        Parameters
        ----------
        uri : str
            The URI to parse for determining the store type.
            The scheme (e.g., 's3://', 'sql://') determines which
            store type to instantiate.

        Returns
        -------
        Store
            The store instance appropriate for handling the given URI.

        Raises
        ------
        KeyError
            If no store is registered for the URI scheme.
        """
        store_type = map_uri_scheme(uri)

        # Build the store instance if not already present
        if store_type not in self._instances:
            store_info = self._builders[store_type]
            store_cls = store_info._store
            cfgrt_cls = store_info._configurator

            if cfgrt_cls is None:
                store = store_cls()
            else:
                store = store_cls(cfgrt_cls())
            self._instances[store_type] = store

        return self._instances[store_type]


store_builder = StoreBuilder()
store_builder.register(SchemeCategory.S3.value, S3Store, S3StoreConfigurator)
store_builder.register(SchemeCategory.SQL.value, SqlStore, SqlStoreConfigurator)
store_builder.register(SchemeCategory.LOCAL.value, LocalStore)
store_builder.register(SchemeCategory.REMOTE.value, RemoteStore)
