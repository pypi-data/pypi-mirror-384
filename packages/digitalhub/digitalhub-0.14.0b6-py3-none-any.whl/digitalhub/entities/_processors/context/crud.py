# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.utils import is_valid_key, sanitize_unversioned_key
from digitalhub.entities._processors.utils import (
    get_context_from_identifier,
    get_context_from_project,
    parse_identifier,
)
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.unversioned.entity import UnversionedEntity


class ContextEntityCRUDProcessor:
    """
    Processor for core CRUD operations on context entities.

    Handles creation, reading, updating, deletion, and listing of
    context-level entities within projects.
    """

    def _create_context_entity(
        self,
        context: Context,
        entity_type: str,
        entity_dict: dict,
    ) -> dict:
        """
        Create a context entity in the backend.

        Builds the appropriate API endpoint and sends a create request
        to the backend for context-level entities within a project.

        Parameters
        ----------
        context : Context
            The project context instance.
        entity_type : str
            The type of entity to create (e.g., 'artifact', 'function').
        entity_dict : dict
            The entity data dictionary to create.

        Returns
        -------
        dict
            The created entity data returned from the backend.
        """
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.CREATE.value,
            project=context.name,
            entity_type=entity_type,
        )
        return context.client.create_object(api, entity_dict)

    def create_context_entity(
        self,
        _entity: ContextEntity | None = None,
        **kwargs,
    ) -> ContextEntity:
        """
        Create a context entity in the backend.

        Creates a new context entity either from an existing entity object
        or by building one from the provided parameters. Handles entity
        creation within a project context.

        Parameters
        ----------
        _entity : ContextEntity
            An existing context entity object to create. If None,
            a new entity will be built from kwargs.
        **kwargs : dict
            Parameters for entity creation, including 'project' and
            entity-specific parameters.

        Returns
        -------
        ContextEntity
            The created context entity with backend data populated.
        """
        if _entity is not None:
            context = _entity._context()
            obj = _entity
        else:
            context = get_context_from_project(kwargs["project"])
            obj: ContextEntity = entity_factory.build_entity_from_params(**kwargs)
        new_obj = self._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        return entity_factory.build_entity_from_dict(new_obj)

    def _read_context_entity(
        self,
        context: Context,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Read a context entity from the backend.

        Retrieves entity data from the backend using either entity ID
        for direct access or entity name for latest version lookup.
        Handles both specific version reads and latest version queries.

        Parameters
        ----------
        context : Context
            The project context instance.
        identifier : str
            Entity key (store://...) or entity name identifier.
        entity_type : str
            The type of entity to read.
        project : str
            Project name (used for identifier parsing).
        entity_id : str
            Specific entity ID to read.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            The entity data retrieved from the backend.
        """
        project, entity_type, _, entity_name, entity_id = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        if entity_id is None:
            kwargs["name"] = entity_name
        kwargs = context.client.build_parameters(
            ApiCategories.CONTEXT.value,
            BackendOperations.READ.value,
            **kwargs,
        )

        if entity_id is None:
            api = context.client.build_api(
                ApiCategories.CONTEXT.value,
                BackendOperations.LIST.value,
                project=context.name,
                entity_type=entity_type,
            )
            return context.client.list_first_object(api, **kwargs)

        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.READ.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.read_object(api, **kwargs)

    def read_context_entity(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> ContextEntity:
        """
        Read a context entity from the backend.

        Retrieves entity data from the backend and constructs a context
        entity object. Handles post-processing for metrics and file info.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name identifier.
        entity_type : str
            The type of entity to read.
        project : str
            Project name for context resolution.
        entity_id : str
            Specific entity ID to read.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        ContextEntity
            The context entity object populated with backend data.
        """
        context = get_context_from_identifier(identifier, project)
        obj = self._read_context_entity(
            context,
            identifier,
            entity_type=entity_type,
            project=project,
            entity_id=entity_id,
            **kwargs,
        )
        entity = entity_factory.build_entity_from_dict(obj)
        return self._post_process_get(entity)

    def read_unversioned_entity(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> UnversionedEntity:
        """
        Read an unversioned entity from the backend.

        Retrieves unversioned entity data (runs, tasks) from the backend.
        Handles identifier parsing for entities that don't follow the
        standard versioned naming convention.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity ID.
        entity_type : str
            The type of entity to read.
        project : str
            Project name for context resolution.
        entity_id : str
            Specific entity ID to read.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        UnversionedEntity
            The unversioned entity object populated with backend data.
        """
        if not is_valid_key(identifier):
            entity_id = identifier
        else:
            identifier = sanitize_unversioned_key(identifier)
        return self.read_context_entity(
            identifier,
            entity_type=entity_type,
            project=project,
            entity_id=entity_id,
            **kwargs,
        )

    def _read_context_entity_versions(
        self,
        context: Context,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        Read all versions of a context entity from the backend.

        Retrieves all available versions of a named entity from the
        backend using the entity name identifier.

        Parameters
        ----------
        context : Context
            The project context instance.
        identifier : str
            Entity key (store://...) or entity name identifier.
        entity_type : str
            The type of entity to read versions for.
        project : str
            Project name (used for identifier parsing).
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        list[dict]
            List of entity data dictionaries for all versions.
        """
        project, entity_type, _, entity_name, _ = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
        )

        kwargs = context.client.build_parameters(
            ApiCategories.CONTEXT.value,
            BackendOperations.READ_ALL_VERSIONS.value,
            name=entity_name,
            **kwargs,
        )

        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.LIST.value,
            project=context.name,
            entity_type=entity_type,
        )
        return context.client.list_objects(api, **kwargs)

    def read_context_entity_versions(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        **kwargs,
    ) -> list[ContextEntity]:
        """
        Read all versions of a context entity from the backend.

        Retrieves all available versions of a named entity and constructs
        context entity objects for each version. Applies post-processing
        for metrics and file info.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name identifier.
        entity_type : str
            The type of entity to read versions for.
        project : str
            Project name for context resolution.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        list[ContextEntity]
            List of context entity objects for all versions.
        """
        context = get_context_from_identifier(identifier, project)
        objs = self._read_context_entity_versions(
            context,
            identifier,
            entity_type=entity_type,
            project=project,
            **kwargs,
        )
        objects = []
        for o in objs:
            entity: ContextEntity = entity_factory.build_entity_from_dict(o)
            entity = self._post_process_get(entity)
            objects.append(entity)
        return objects

    def _list_context_entities(
        self,
        context: Context,
        entity_type: str,
        **kwargs,
    ) -> list[dict]:
        """
        List context entities from the backend.

        Retrieves a list of entities of a specific type from the backend
        within the project context.

        Parameters
        ----------
        context : Context
            The project context instance.
        entity_type : str
            The type of entities to list.
        **kwargs : dict
            Additional parameters to pass to the API call for filtering
            or pagination.

        Returns
        -------
        list[dict]
            List of entity data dictionaries from the backend.
        """
        kwargs = context.client.build_parameters(
            ApiCategories.CONTEXT.value,
            BackendOperations.LIST.value,
            **kwargs,
        )
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.LIST.value,
            project=context.name,
            entity_type=entity_type,
        )
        return context.client.list_objects(api, **kwargs)

    def list_context_entities(
        self,
        project: str,
        entity_type: str,
        **kwargs,
    ) -> list[ContextEntity]:
        """
        List all latest version context entities from the backend.

        Retrieves a list of entities of a specific type from the backend
        and constructs context entity objects. Only returns the latest
        version of each entity. Applies post-processing for metrics and
        file info.

        Parameters
        ----------
        project : str
            The project name to list entities from.
        entity_type : str
            The type of entities to list.
        **kwargs : dict
            Additional parameters to pass to the API call for filtering
            or pagination.

        Returns
        -------
        list[ContextEntity]
            List of context entity objects (latest versions only).
        """
        context = get_context_from_project(project)
        objs = self._list_context_entities(context, entity_type, **kwargs)
        objects = []
        for o in objs:
            entity: ContextEntity = entity_factory.build_entity_from_dict(o)
            entity = self._post_process_get(entity)
            objects.append(entity)
        return objects

    def _update_context_entity(
        self,
        context: Context,
        entity_type: str,
        entity_id: str,
        entity_dict: dict,
        **kwargs,
    ) -> dict:
        """
        Update a context entity in the backend.

        Updates an existing context entity with new data. Entity
        specifications are typically immutable, so this primarily
        updates status and metadata.

        Parameters
        ----------
        context : Context
            The project context instance.
        entity_type : str
            The type of entity to update.
        entity_id : str
            The unique identifier of the entity to update.
        entity_dict : dict
            The updated entity data dictionary.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            Response data from the backend update operation.
        """
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.UPDATE.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.update_object(api, entity_dict, **kwargs)

    def update_context_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        entity_dict: dict,
        **kwargs,
    ) -> ContextEntity:
        """
        Update a context entity in the backend.

        Updates an existing context entity with new data and returns
        the updated context entity object. Entity specifications are
        typically immutable.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity to update.
        entity_id : str
            The unique identifier of the entity to update.
        entity_dict : dict
            The updated entity data dictionary.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        ContextEntity
            The updated context entity object.
        """
        context = get_context_from_project(project)
        obj = self._update_context_entity(
            context,
            entity_type,
            entity_id,
            entity_dict,
            **kwargs,
        )
        return entity_factory.build_entity_from_dict(obj)

    def _delete_context_entity(
        self,
        context: Context,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Delete a context entity from the backend.

        Removes an entity from the backend, with options for deleting
        specific versions or all versions of a named entity. Handles
        cascade deletion if supported.

        Parameters
        ----------
        context : Context
            The project context instance.
        identifier : str
            Entity key (store://...) or entity name identifier.
        entity_type : str
            The type of entity to delete.
        project : str
            Project name (used for identifier parsing).
        entity_id : str
            Specific entity ID to delete.
        **kwargs : dict
            Additional parameters including:
            - 'delete_all_versions': delete all versions of named entity
            - 'cascade': cascade deletion options

        Returns
        -------
        dict
            Response data from the backend delete operation.
        """
        project, entity_type, _, entity_name, entity_id = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        delete_all_versions: bool = kwargs.pop("delete_all_versions", False)
        if delete_all_versions:
            op = BackendOperations.DELETE_ALL_VERSIONS.value
            kwargs["name"] = entity_name
        else:
            if entity_id is None:
                raise ValueError("If `delete_all_versions` is False, `entity_id` must be provided.")
            op = BackendOperations.DELETE.value

        kwargs = context.client.build_parameters(
            ApiCategories.CONTEXT.value,
            op,
            **kwargs,
        )

        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            op,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.delete_object(api, **kwargs)

    def delete_context_entity(
        self,
        identifier: str,
        project: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Delete a context entity from the backend.

        Removes an entity from the backend with support for deleting
        specific versions or all versions of a named entity.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name identifier.
        project : str
            Project name for context resolution.
        entity_type : str
            The type of entity to delete.
        entity_id : str
            Specific entity ID to delete.
        **kwargs : dict
            Additional parameters including deletion options.

        Returns
        -------
        dict
            Response data from the backend delete operation.
        """
        context = get_context_from_identifier(identifier, project)
        return self._delete_context_entity(
            context,
            identifier,
            entity_type,
            context.name,
            entity_id,
            **kwargs,
        )

    def _post_process_get(self, entity: ContextEntity) -> ContextEntity:
        """
        Post-process a retrieved context entity.

        Applies additional processing to entities after retrieval,
        including loading metrics and file information if available.

        Parameters
        ----------
        entity : ContextEntity
            The entity to post-process.

        Returns
        -------
        ContextEntity
            The post-processed entity with additional data loaded.
        """
        if hasattr(entity.status, "metrics"):
            entity._get_metrics()
        if hasattr(entity.status, "files"):
            entity._get_files_info()
        return entity
