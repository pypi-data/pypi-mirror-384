# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod
from typing import Any

if typing.TYPE_CHECKING:
    from digitalhub.stores.client._base.api_builder import ClientApiBuilder
    from digitalhub.stores.client._base.key_builder import ClientKeyBuilder
    from digitalhub.stores.client._base.params_builder import ClientParametersBuilder


class Client:
    """
    Base Client class interface.

    The client is an interface that handles the CRUD of an object during
    a session. It manages the creation, reading, updating, deleting and
    listing of objects and comes into two subclasses: Local and DHCore.
    """

    def __init__(self) -> None:
        self._api_builder: ClientApiBuilder = None
        self._key_builder: ClientKeyBuilder = None
        self._params_builder: ClientParametersBuilder = None

    ##############################
    # CRUD methods
    ##############################

    @abstractmethod
    def create_object(self, api: str, obj: Any, **kwargs) -> dict:
        """
        Create object method.

        Parameters
        ----------
        api : str
            The API endpoint to create the object.
        obj : Any
            The object to create.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        dict
            The created object.
        """

    @abstractmethod
    def read_object(self, api: str, **kwargs) -> dict:
        """
        Read object method.

        Parameters
        ----------
        api : str
            The API endpoint to read the object.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        dict
            The retrieved object.
        """

    @abstractmethod
    def update_object(self, api: str, obj: Any, **kwargs) -> dict:
        """
        Update object method.

        Parameters
        ----------
        api : str
            The API endpoint to update the object.
        obj : Any
            The object to update.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        dict
            The updated object.
        """

    @abstractmethod
    def delete_object(self, api: str, **kwargs) -> dict:
        """
        Delete object method.

        Parameters
        ----------
        api : str
            The API endpoint to delete the object.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        dict
            The deletion result.
        """

    @abstractmethod
    def list_objects(self, api: str, **kwargs) -> dict:
        """
        List objects method.

        Parameters
        ----------
        api : str
            The API endpoint to list objects.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        dict
            The list of objects.
        """

    @abstractmethod
    def list_first_object(self, api: str, **kwargs) -> dict:
        """
        Read first object method.

        Parameters
        ----------
        api : str
            The API endpoint to read the first object.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        dict
            The first object in the list.
        """

    @abstractmethod
    def search_objects(self, api: str, **kwargs) -> dict:
        """
        Search objects method.

        Parameters
        ----------
        api : str
            The API endpoint to search objects.
        **kwargs : dict
            Additional keyword arguments containing search parameters.

        Returns
        -------
        dict
            The search results.
        """

    ##############################
    # Build methods
    ##############################

    def build_api(self, category: str, operation: str, **kwargs) -> str:
        """
        Build the API for the client.

        Parameters
        ----------
        category : str
            API category.
        operation : str
            API operation.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            API formatted.
        """
        return self._api_builder.build_api(category, operation, **kwargs)

    def build_key(self, category: str, *args, **kwargs) -> str:
        """
        Build the key for the client.

        Parameters
        ----------
        category : str
            Key category.
        *args : tuple
            Additional arguments.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            Key formatted.
        """
        return self._key_builder.build_key(category, *args, **kwargs)

    def build_parameters(self, category: str, operation: str, **kwargs) -> dict:
        """
        Build the parameters for the client call.

        Parameters
        ----------
        category : str
            API category.
        operation : str
            API operation.
        **kwargs : dict
            Parameters to build.

        Returns
        -------
        dict
            Parameters formatted.
        """
        return self._params_builder.build_parameters(category, operation, **kwargs)

    ##############################
    # Interface methods
    ##############################

    @staticmethod
    @abstractmethod
    def is_local() -> bool:
        """
        Flag to check if client is local.

        Returns
        -------
        bool
            True if the client operates locally, False otherwise.
        """
