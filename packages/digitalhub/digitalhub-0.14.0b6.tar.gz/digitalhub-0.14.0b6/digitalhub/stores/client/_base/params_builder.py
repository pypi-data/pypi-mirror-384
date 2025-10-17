# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod
from typing import Any


class ClientParametersBuilder:
    """
    This class is used to build the parameters for the client call.
    Depending on the client, the parameters are built differently.
    """

    @abstractmethod
    def build_parameters(self, category: str, operation: str, **kwargs) -> dict:
        """
        Build the parameters for the client call.

        Parameters
        ----------
        category : str
            The API category.
        operation : str
            The API operation.
        **kwargs : dict
            Additional keyword arguments to build parameters from.

        Returns
        -------
        dict
            The formatted parameters for the client call.
        """

    @staticmethod
    def _ensure_params(**kwargs) -> dict:
        """
        Initialize parameter dictionary with query parameters structure.

        Ensures parameter dictionary has 'params' key for HTTP query parameters,
        guaranteeing consistent structure for all parameter building methods.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Parameters dictionary with guaranteed 'params' key containing
            empty dict if not already present.
        """
        if "params" not in kwargs:
            kwargs["params"] = {}
        return kwargs

    @staticmethod
    def _add_param(key: str, value: Any | None, **kwargs) -> dict:
        """
        Add a single query parameter to kwargs.

        Parameters
        ----------
        key : str
            Parameter key.
        value : Any
            Parameter value.
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Parameters dictionary with added key-value pair in 'params'.
        """
        kwargs["params"][key] = value
        return kwargs
