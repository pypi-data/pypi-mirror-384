# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._processors.utils import get_context_from_project
from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor


class ContextEntitySpecialOpsProcessor:
    """
    Processor for specialized context entity operations.

    Handles backend operations like secrets management, logging,
    entity control (start/stop/resume), file operations, and metrics.
    """

    def build_context_entity_key(
        self,
        project: str,
        entity_type: str,
        entity_kind: str,
        entity_name: str,
        entity_id: str | None = None,
    ) -> str:
        """
        Build a storage key for a context entity.

        Creates a standardized key string for context entity identification
        and storage, resolving the project context automatically.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity.
        entity_kind : str
            The kind/subtype of entity.
        entity_name : str
            The name of the entity.
        entity_id : str
            The unique identifier of the entity version.

        Returns
        -------
        str
            The constructed context entity key string.
        """
        context = get_context_from_project(project)
        return context.client.build_key(
            ApiCategories.CONTEXT.value,
            project=context.name,
            entity_type=entity_type,
            entity_kind=entity_kind,
            entity_name=entity_name,
            entity_id=entity_id,
        )

    def read_secret_data(
        self,
        project: str,
        entity_type: str,
        **kwargs,
    ) -> dict:
        """
        Read secret data from the backend.

        Retrieves secret data stored in the backend for a specific
        project and entity type.

        Parameters
        ----------
        project : str
            The project name containing the secrets.
        entity_type : str
            The type of entity (typically 'secret').
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            Secret data retrieved from the backend.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.DATA.value,
            project=context.name,
            entity_type=entity_type,
        )
        return context.client.read_object(api, **kwargs)

    def update_secret_data(
        self,
        project: str,
        entity_type: str,
        data: dict,
        **kwargs,
    ) -> None:
        """
        Update secret data in the backend.

        Stores or updates secret data in the backend for a specific
        project and entity type.

        Parameters
        ----------
        project : str
            The project name to store secrets in.
        entity_type : str
            The type of entity (typically 'secret').
        data : dict
            The secret data dictionary to store.
        **kwargs : dict
            Additional parameters to pass to the API call.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.DATA.value,
            project=context.name,
            entity_type=entity_type,
        )
        context.client.update_object(api, data, **kwargs)

    def read_run_logs(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> dict:
        """
        Read execution logs from the backend.

        Retrieves logs for a specific run or task execution from
        the backend.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity (typically 'run' or 'task').
        entity_id : str
            The unique identifier of the entity to get logs for.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            Log data retrieved from the backend.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.LOGS.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.read_object(api, **kwargs)

    def stop_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> None:
        """
        Stop a running entity in the backend.

        Sends a stop signal to halt execution of a running entity
        such as a workflow or long-running task.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity to stop.
        entity_id : str
            The unique identifier of the entity to stop.
        **kwargs : dict
            Additional parameters to pass to the API call.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.STOP.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        context.client.create_object(api, **kwargs)

    def resume_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> None:
        """
        Resume a stopped entity in the backend.

        Sends a resume signal to restart execution of a previously
        stopped entity such as a workflow or task.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity to resume.
        entity_id : str
            The unique identifier of the entity to resume.
        **kwargs : dict
            Additional parameters to pass to the API call.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.RESUME.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        context.client.create_object(api, **kwargs)

    def read_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> list[dict]:
        """
        Read file information from the backend.

        Retrieves metadata about files associated with an entity,
        including file paths, sizes, and other attributes.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity to get file info for.
        entity_id : str
            The unique identifier of the entity.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        list[dict]
            List of file information dictionaries from the backend.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.FILES.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.read_object(api, **kwargs)

    def update_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        entity_list: list[dict],
        **kwargs,
    ) -> None:
        """
        Get files info from backend.

        Parameters
        ----------
        project : str
            Project name.
        entity_type : str
            Entity type.
        entity_id : str
            Entity ID.
        entity_list : list[dict]
            Entity list.
        **kwargs : dict
            Parameters to pass to the API call.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.FILES.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.update_object(api, entity_list, **kwargs)

    def read_metrics(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Read metrics from the backend for a specific entity.

        Retrieves metrics data associated with an entity. Can fetch either
        all metrics or a specific metric by name. Used for performance
        monitoring and analysis of entity operations.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity to read metrics from.
        entity_id : str
            The unique identifier of the entity.
        metric_name : str
            The name of a specific metric to retrieve.
            If None, retrieves all available metrics.
        **kwargs : dict
            Additional parameters to pass to the API call.

        Returns
        -------
        dict
            Dictionary containing metric data from the backend.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.METRICS.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
        )
        return context.client.read_object(api, **kwargs)

    def update_metric(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        metric_value: Any,
        **kwargs,
    ) -> None:
        """
        Update or create a metric value for an entity in the backend.

        Updates an existing metric or creates a new one with the specified
        value. Metrics are used for tracking performance, status, and
        other quantitative aspects of entity operations.

        Parameters
        ----------
        project : str
            The project name containing the entity.
        entity_type : str
            The type of entity to update metrics for.
        entity_id : str
            The unique identifier of the entity.
        metric_name : str
            The name of the metric to update or create.
        metric_value : Any
            The value to set for the metric.
            Can be numeric, string, or other supported types.
        **kwargs : dict
            Additional parameters to pass to the API call.
        """
        context = get_context_from_project(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.METRICS.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
        )
        context.client.update_object(api, metric_value, **kwargs)

    def search_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        project: str,
        query: str | None = None,
        entity_types: list[str] | None = None,
        name: str | None = None,
        kind: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> list[ContextEntity]:
        """
        Search for entities in the backend using various criteria.

        Performs a flexible search across multiple entity attributes,
        allowing for complex queries and filtering. Returns matching
        entities from the project context.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        project : str
            The project name to search within.
        query : str
            Free-text search query to match against entity content.
        entity_types : list[str]
            List of entity types to filter by.
            If None, searches all entity types.
        name : str
            Entity name pattern to match.
        kind : str
            Entity kind to filter by.
        created : str
            Creation date filter (ISO format).
        updated : str
            Last update date filter (ISO format).
        description : str
            Description pattern to match.
        labels : list[str]
            List of label patterns to match.
        **kwargs : dict
            Additional search parameters to pass to the API call.

        Returns
        -------
        list[ContextEntity]
            List of matching entity instances from the search.
        """
        context = get_context_from_project(project)
        kwargs = context.client.build_parameters(
            ApiCategories.CONTEXT.value,
            BackendOperations.SEARCH.value,
            query=query,
            entity_types=entity_types,
            name=name,
            kind=kind,
            created=created,
            updated=updated,
            description=description,
            labels=labels,
            **kwargs,
        )
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.SEARCH.value,
            project=context.name,
        )
        entities_dict = context.client.read_object(api, **kwargs)
        return [crud_processor.read_context_entity(entity["key"]) for entity in entities_dict["content"]]
