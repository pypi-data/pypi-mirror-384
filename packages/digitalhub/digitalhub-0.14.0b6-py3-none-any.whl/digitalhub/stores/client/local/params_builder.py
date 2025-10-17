# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.stores.client._base.params_builder import ClientParametersBuilder


class ClientLocalParametersBuilder(ClientParametersBuilder):
    """
    This class is used to build the parameters for the Local client calls.
    """

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
        if category == ApiCategories.BASE.value:
            return self.build_parameters_base(operation, **kwargs)
        return self.build_parameters_context(operation, **kwargs)

    def build_parameters_base(self, operation: str, **kwargs) -> dict:
        """
        Build the base parameters for the client call.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Parameters to build.

        Returns
        -------
        dict
            Parameters formatted.
        """
        kwargs = self._ensure_params(**kwargs)

        # Handle delete
        if operation == BackendOperations.DELETE.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = self._add_param("cascade", str(cascade).lower(), **kwargs)

        return kwargs

    def build_parameters_context(self, operation: str, **kwargs) -> dict:
        """
        Build the context parameters for the client call.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Parameters to build.

        Returns
        -------
        dict
            Parameters formatted.
        """
        kwargs = self._ensure_params(**kwargs)

        # Handle read all versions
        if operation == BackendOperations.READ_ALL_VERSIONS.value:
            kwargs = self._add_param("versions", "all", **kwargs)
            kwargs = self._add_param("name", kwargs.pop("name"), **kwargs)

        # Handle delete
        elif operation == BackendOperations.DELETE.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = self._add_param("cascade", str(cascade).lower(), **kwargs)

        # Handle delete all versions
        elif operation == BackendOperations.DELETE_ALL_VERSIONS.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = self._add_param("cascade", str(cascade).lower(), **kwargs)
            kwargs = self._add_param("name", kwargs.pop("name"), **kwargs)

        return kwargs
