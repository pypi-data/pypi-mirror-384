# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client._base.api_builder import ClientApiBuilder
from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.stores.client.local.enums import LocalClientVar
from digitalhub.utils.exceptions import BackendError

API_BASE = "/api/v1"
API_CONTEXT = f"{API_BASE}/-"


class ClientLocalApiBuilder(ClientApiBuilder):
    """
    This class is used to build the API for the Local client.
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
        raise BackendError(f"API for operation '{operation}' for entity type '{entity_type}' not implemented in Local.")

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
        try:
            entity_type = kwargs["entity_type"] + "s"
        except KeyError:
            pass
        project = kwargs["project"]
        if operation in (
            BackendOperations.CREATE.value,
            BackendOperations.LIST.value,
        ):
            return f"{API_CONTEXT}/{project}/{entity_type}"
        elif operation in (
            BackendOperations.READ.value,
            BackendOperations.UPDATE.value,
            BackendOperations.DELETE.value,
        ):
            return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}"
        elif operation in (
            BackendOperations.LOGS.value,
            BackendOperations.FILES.value,
            BackendOperations.METRICS.value,
        ):
            return LocalClientVar.EMPTY.value
        raise BackendError(f"API for operation '{operation}' for entity type '{entity_type}' not implemented in Local.")
