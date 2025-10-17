# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.api import delete_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.stores.client.api import get_client

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project
    from digitalhub.stores.client._base.client import Client


class BaseEntityCRUDProcessor:
    """
    Processor for core CRUD operations on base entities.

    Handles creation, reading, updating, deletion, and listing of
    base-level entities (primarily projects) within the backend.
    """

    def _create_base_entity(
        self,
        client: Client,
        entity_type: str,
        entity_dict: dict,
        **kwargs,
    ) -> dict:
        """
        Create a base entity in the backend.

        Builds the appropriate API endpoint and sends a create request
        to the backend for base-level entities.

        Parameters
        ----------
        client : Client
            The client instance to use for the API call.
        entity_type : str
            The type of entity to create (e.g., 'project').
        entity_dict : dict
            The entity data dictionary to create.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            The created entity data returned from the backend.
        """
        api = client.build_api(
            ApiCategories.BASE.value,
            BackendOperations.CREATE.value,
            entity_type=entity_type,
        )
        return client.create_object(api, entity_dict, **kwargs)

    def create_project_entity(
        self,
        _entity: Project | None = None,
        **kwargs,
    ) -> Project:
        """
        Create a project entity in the backend.

        Creates a new project either from an existing entity object or
        by building one from the provided parameters. Handles both
        local and remote backend creation.

        Parameters
        ----------
        _entity : Project
            An existing project entity object to create. If None,
            a new entity will be built from kwargs.
        **kwargs : dict
            Parameters for entity creation, including 'local' flag
            and entity-specific parameters.

        Returns
        -------
        Project
            The created project entity with backend data populated.
        """
        if _entity is not None:
            client = _entity._client
            obj = _entity
        else:
            client = get_client(kwargs.get("local"))
            obj = entity_factory.build_entity_from_params(**kwargs)
        ent = self._create_base_entity(client, obj.ENTITY_TYPE, obj.to_dict())
        ent["local"] = client.is_local()
        return entity_factory.build_entity_from_dict(ent)

    def _read_base_entity(
        self,
        client: Client,
        entity_type: str,
        entity_name: str,
        **kwargs,
    ) -> dict:
        """
        Read a base entity from the backend.

        Builds the appropriate API endpoint and sends a read request
        to retrieve entity data from the backend.

        Parameters
        ----------
        client : Client
            The client instance to use for the API call.
        entity_type : str
            The type of entity to read (e.g., 'project').
        entity_name : str
            The name identifier of the entity to read.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            The entity data retrieved from the backend.
        """
        api = client.build_api(
            ApiCategories.BASE.value,
            BackendOperations.READ.value,
            entity_type=entity_type,
            entity_name=entity_name,
        )
        return client.read_object(api, **kwargs)

    def read_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        **kwargs,
    ) -> Project:
        """
        Read a project entity from the backend.

        Retrieves project data from the backend and constructs a
        Project entity object with the retrieved data.

        Parameters
        ----------
        entity_type : str
            The type of entity to read (typically 'project').
        entity_name : str
            The name identifier of the project to read.
        **kwargs : dict
            Additional parameters including 'local' flag and
            API call parameters.

        Returns
        -------
        Project
            The project entity object populated with backend data.
        """
        client = get_client(kwargs.pop("local", False))
        obj = self._read_base_entity(client, entity_type, entity_name, **kwargs)
        obj["local"] = client.is_local()
        return entity_factory.build_entity_from_dict(obj)

    def _list_base_entities(
        self,
        client: Client,
        entity_type: str,
        **kwargs,
    ) -> list[dict]:
        """
        List base entities from the backend.

        Builds the appropriate API endpoint and sends a list request
        to retrieve multiple entities from the backend.

        Parameters
        ----------
        client : Client
            The client instance to use for the API call.
        entity_type : str
            The type of entities to list (e.g., 'project').
        **kwargs : dict
            Additional parameters to pass to the API call for filtering
            or pagination.

        Returns
        -------
        list[dict]
            List of entity data dictionaries from the backend.
        """
        api = client.build_api(
            ApiCategories.BASE.value,
            BackendOperations.LIST.value,
            entity_type=entity_type,
        )
        return client.list_objects(api, **kwargs)

    def list_project_entities(
        self,
        entity_type: str,
        **kwargs,
    ) -> list[Project]:
        """
        List project entities from the backend.

        Retrieves a list of projects from the backend and converts
        them to Project entity objects.

        Parameters
        ----------
        entity_type : str
            The type of entities to list (typically 'project').
        **kwargs : dict
            Additional parameters including 'local' flag and
            API call parameters for filtering or pagination.

        Returns
        -------
        list[Project]
            List of project entity objects.
        """
        client = get_client(kwargs.pop("local", False))
        objs = self._list_base_entities(client, entity_type, **kwargs)
        entities = []
        for obj in objs:
            obj["local"] = client.is_local()
            ent = entity_factory.build_entity_from_dict(obj)
            entities.append(ent)
        return entities

    def _update_base_entity(
        self,
        client: Client,
        entity_type: str,
        entity_name: str,
        entity_dict: dict,
        **kwargs,
    ) -> dict:
        """
        Update a base entity in the backend.

        Builds the appropriate API endpoint and sends an update request
        to modify an existing entity in the backend.

        Parameters
        ----------
        client : Client
            The client instance to use for the API call.
        entity_type : str
            The type of entity to update (e.g., 'project').
        entity_name : str
            The name identifier of the entity to update.
        entity_dict : dict
            The updated entity data dictionary.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            The updated entity data returned from the backend.
        """
        api = client.build_api(
            ApiCategories.BASE.value,
            BackendOperations.UPDATE.value,
            entity_type=entity_type,
            entity_name=entity_name,
        )
        return client.update_object(api, entity_dict, **kwargs)

    def update_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        entity_dict: dict,
        **kwargs,
    ) -> Project:
        """
        Update a project entity in the backend.

        Updates an existing project with new data and returns the
        updated Project entity object.

        Parameters
        ----------
        entity_type : str
            The type of entity to update (typically 'project').
        entity_name : str
            The name identifier of the project to update.
        entity_dict : dict
            The updated project data dictionary.
        **kwargs : dict
            Additional parameters including 'local' flag and
            API call parameters.

        Returns
        -------
        Project
            The updated project entity object.
        """
        client = get_client(kwargs.pop("local", False))
        obj = self._update_base_entity(client, entity_type, entity_name, entity_dict, **kwargs)
        obj["local"] = client.is_local()
        return entity_factory.build_entity_from_dict(obj)

    def _delete_base_entity(
        self,
        client: Client,
        entity_type: str,
        entity_name: str,
        **kwargs,
    ) -> dict:
        """
        Delete a base entity from the backend.

        Builds the appropriate API endpoint and parameters, then sends
        a delete request to remove the entity from the backend.

        Parameters
        ----------
        client : Client
            The client instance to use for the API call.
        entity_type : str
            The type of entity to delete (e.g., 'project').
        entity_name : str
            The name identifier of the entity to delete.
        **kwargs : dict
            Additional parameters to pass to the API call, such as
            cascade deletion options.

        Returns
        -------
        dict
            Response data from the backend delete operation.
        """
        kwargs = client.build_parameters(
            ApiCategories.BASE.value,
            BackendOperations.DELETE.value,
            **kwargs,
        )
        api = client.build_api(
            ApiCategories.BASE.value,
            BackendOperations.DELETE.value,
            entity_type=entity_type,
            entity_name=entity_name,
        )
        return client.delete_object(api, **kwargs)

    def delete_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        **kwargs,
    ) -> dict:
        """
        Delete a project entity from the backend.

        Deletes a project from the backend and optionally cleans up
        the associated context. Handles both local and remote backends.

        Parameters
        ----------
        crud_processor : BaseEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        entity_type : str
            The type of entity to delete (typically 'project').
        entity_name : str
            The name identifier of the project to delete.
        **kwargs : dict
            Additional parameters including 'local' flag, 'clean_context'
            flag (default True), and API call parameters.

        Returns
        -------
        dict
            Response data from the backend delete operation.
        """
        if kwargs.pop("clean_context", True):
            delete_context(entity_name)
        client = get_client(kwargs.pop("local", False))
        return self._delete_base_entity(
            client,
            entity_type,
            entity_name,
            **kwargs,
        )
