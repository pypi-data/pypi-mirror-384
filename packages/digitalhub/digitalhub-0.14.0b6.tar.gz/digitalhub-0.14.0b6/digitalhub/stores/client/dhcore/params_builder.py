# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.stores.client._base.params_builder import ClientParametersBuilder

DEFAULT_START_PAGE = 0
DEFAULT_SIZE = 25
DEFAULT_SORT = "metadata.updated,DESC"


class ClientDHCoreParametersBuilder(ClientParametersBuilder):
    """
    Parameter builder for DHCore client API calls.

    Constructs HTTP request parameters for DHCore API operations, handling
    parameter formats and query structures for both base-level operations
    (project management) and context-level operations (entity operations
    within projects). Supports query parameter formatting, search filter
    construction for Solr-based searches, cascade deletion options,
    versioning parameters, and entity sharing parameters.

    Methods
    -------
    build_parameters(category, operation, **kwargs)
        Main entry point for parameter building based on API category.
    build_parameters_base(operation, **kwargs)
        Builds parameters for base-level API operations.
    build_parameters_context(operation, **kwargs)
        Builds parameters for context-level API operations.
    """

    def build_parameters(self, category: str, operation: str, **kwargs) -> dict:
        """
        Build HTTP request parameters for DHCore API calls.

        Parameters
        ----------
        category : str
            API category: 'base' for project-level operations or 'context'
            for entity operations within projects.
        operation : str
            Specific API operation (create, read, update, delete, list, search, etc.).
        **kwargs : dict
            Raw parameters to transform including entity identifiers, filter
            criteria, pagination options, etc.

        Returns
        -------
        dict
            Formatted parameters dictionary with 'params' key for query parameters
            and other request-specific parameters.
        """
        if category == ApiCategories.BASE.value:
            return self.build_parameters_base(operation, **kwargs)
        return self.build_parameters_context(operation, **kwargs)

    def build_parameters_base(self, operation: str, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for project operations.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Operation-specific parameters.
        Returns
        -------
        dict
            Formatted parameters with 'params' containing query parameters.
        """
        kwargs = self._ensure_params(**kwargs)

        # Handle delete
        if operation == BackendOperations.DELETE.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = self._add_param("cascade", str(cascade).lower(), **kwargs)

        # Handle share
        elif operation == BackendOperations.SHARE.value:
            kwargs = self._add_param("user", kwargs.pop("user"), **kwargs)
            if kwargs.pop("unshare", False):
                kwargs = self._add_param("id", kwargs.pop("id"), **kwargs)

        return kwargs

    def build_parameters_context(self, operation: str, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for entity management and search within
        projects.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Operation-specific parameters.

        Returns
        -------
        dict
            Formatted parameters with 'params'.
        """
        kwargs = self._ensure_params(**kwargs)

        # Handle read
        if operation == BackendOperations.READ.value:
            if (name := kwargs.pop("name", None)) is not None:
                kwargs = self._add_param("name", name, **kwargs)

        # Handle read all versions
        elif operation == BackendOperations.READ_ALL_VERSIONS.value:
            kwargs = self._add_param("versions", "all", **kwargs)
            kwargs = self._add_param("name", kwargs.pop("name"), **kwargs)

        # Handle list
        elif operation == BackendOperations.LIST.value:
            possible_list_params = [
                "q",
                "name",
                "kind",
                "user",
                "state",
                "created",
                "updated",
                "versions",
                "function",
                "workflow",
                "action",
                "task",
            ]
            list_params = {k: kwargs.get(k, None) for k in possible_list_params}
            list_params = self._filter_none_params(**list_params)
            for k, v in list_params.items():
                kwargs = self._add_param(k, v, **kwargs)
            for k in possible_list_params:
                kwargs.pop(k, None)

        # Handle delete
        elif operation == BackendOperations.DELETE.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = self._add_param("cascade", str(cascade).lower(), **kwargs)

        elif operation == BackendOperations.DELETE_ALL_VERSIONS.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = self._add_param("cascade", str(cascade).lower(), **kwargs)
            kwargs = self._add_param("name", kwargs.pop("name"), **kwargs)

        # Handle search
        elif operation == BackendOperations.SEARCH.value:
            # Handle fq
            if (fq := kwargs.pop("fq", None)) is not None:
                kwargs = self._add_param("fq", fq, **kwargs)

            # Add search query
            if (query := kwargs.pop("query", None)) is not None:
                kwargs = self._add_param("q", query, **kwargs)

            # Add search filters
            fq = []

            # Entity types
            if (entity_types := kwargs.pop("entity_types", None)) is not None:
                if not isinstance(entity_types, list):
                    entity_types = [entity_types]
                if len(entity_types) == 1:
                    entity_types = entity_types[0]
                else:
                    entity_types = " OR ".join(entity_types)
                fq.append(f"type:({entity_types})")

            # Name
            if (name := kwargs.pop("name", None)) is not None:
                fq.append(f'metadata.name:"{name}"')

            # Kind
            if (kind := kwargs.pop("kind", None)) is not None:
                fq.append(f'kind:"{kind}"')

            # Time
            created = kwargs.pop("created", None)
            updated = kwargs.pop("updated", None)
            created = created if created is not None else "*"
            updated = updated if updated is not None else "*"
            fq.append(f"metadata.updated:[{created} TO {updated}]")

            # Description
            if (description := kwargs.pop("description", None)) is not None:
                fq.append(f'metadata.description:"{description}"')

            # Labels
            if (labels := kwargs.pop("labels", None)) is not None:
                if len(labels) == 1:
                    labels = labels[0]
                else:
                    labels = " AND ".join(labels)
                fq.append(f"metadata.labels:({labels})")

            # Add filters
            kwargs = self._add_param("fq", fq, **kwargs)

        return kwargs

    def set_pagination(self, partial: bool = False, **kwargs) -> dict:
        """
        Ensure pagination parameters are set in kwargs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Pagination parameters set in 'params' of kwargs.
        """
        kwargs = self._ensure_params(**kwargs)

        if "page" not in kwargs["params"]:
            kwargs["params"]["page"] = DEFAULT_START_PAGE

        if partial:
            return kwargs

        if "size" not in kwargs["params"]:
            kwargs["params"]["size"] = DEFAULT_SIZE

        if "sort" not in kwargs["params"]:
            kwargs["params"]["sort"] = DEFAULT_SORT

        return kwargs

    @staticmethod
    def read_page_number(**kwargs) -> int:
        """
        Read current page number from kwargs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        int
            Current page number.
        """
        return kwargs["params"]["page"]

    @staticmethod
    def increment_page_number(**kwargs) -> dict:
        """
        Increment page number in kwargs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Parameters dictionary with incremented 'page' number in 'params'.
        """
        kwargs["params"]["page"] += 1
        return kwargs

    @staticmethod
    def _filter_none_params(**kwargs) -> dict:
        """
        Filter out None values from kwargs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to filter.

        Returns
        -------
        dict
            Filtered kwargs.
        """
        return {k: v for k, v in kwargs.items() if v is not None}
