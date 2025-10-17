# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client._base.api_builder import ClientApiBuilder
from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.utils.exceptions import BackendError

API_BASE = "/api/v1"
API_CONTEXT = f"{API_BASE}/-"


class ClientDHCoreApiBuilder(ClientApiBuilder):
    """
    This class is used to build the API for the DHCore client.
    """

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
        if category == ApiCategories.BASE.value:
            return self.build_api_base(operation, **kwargs)
        return self.build_api_context(operation, **kwargs)

    def build_api_base(self, operation: str, **kwargs) -> str:
        """
        Build the base API for the client.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            API formatted.
        """
        entity_type = kwargs["entity_type"] + "s"
        if operation in (
            BackendOperations.CREATE.value,
            BackendOperations.LIST.value,
        ):
            return f"{API_BASE}/{entity_type}"
        elif operation in (
            BackendOperations.READ.value,
            BackendOperations.UPDATE.value,
            BackendOperations.DELETE.value,
        ):
            return f"{API_BASE}/{entity_type}/{kwargs['entity_name']}"
        elif operation == BackendOperations.SHARE.value:
            return f"{API_BASE}/{entity_type}/{kwargs['entity_name']}/share"
        raise BackendError(f"Invalid operation '{operation}' for entity type '{entity_type}' in DHCore.")

    def build_api_context(self, operation: str, **kwargs) -> str:
        """
        Build the context API for the client.

        Parameters
        ----------
        operation : str
            The API operation.
        **kwargs : dict
            Additional parameters including project, entity_type, entity_id, etc.

        Returns
        -------
        str
            The formatted context API endpoint.

        Raises
        ------
        BackendError
            If the operation is not supported for the entity type.
        """
        project = kwargs["project"]
        if operation == BackendOperations.SEARCH.value:
            return f"{API_CONTEXT}/{project}/solr/search/item"

        entity_type = kwargs["entity_type"] + "s"
        if operation in (
            BackendOperations.CREATE.value,
            BackendOperations.LIST.value,
            BackendOperations.DELETE_ALL_VERSIONS.value,
        ):
            return f"{API_CONTEXT}/{project}/{entity_type}"
        elif operation in (
            BackendOperations.READ.value,
            BackendOperations.UPDATE.value,
            BackendOperations.DELETE.value,
        ):
            return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}"
        elif operation == BackendOperations.LOGS.value:
            return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}/logs"
        elif operation == BackendOperations.STOP.value:
            return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}/stop"
        elif operation == BackendOperations.RESUME.value:
            return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}/resume"
        elif operation == BackendOperations.DATA.value:
            return f"{API_CONTEXT}/{project}/{entity_type}/data"
        elif operation == BackendOperations.FILES.value:
            return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}/files/info"
        elif operation == BackendOperations.METRICS.value:
            if kwargs["metric_name"] is not None:
                return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}/metrics/{kwargs['metric_name']}"
            else:
                return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}/metrics"

        raise BackendError(f"Invalid operation '{operation}' for entity type '{entity_type}' in DHCore.")
