# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod


class ClientApiBuilder:
    """
    This class is used to build the API for the client.
    Depending on the client, the API is built differently.
    """

    @abstractmethod
    def build_api(self, category: str, operation: str, **kwargs) -> str:
        """
        Build the API for the client.

        Parameters
        ----------
        category : str
            The API category.
        operation : str
            The API operation.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        str
            The formatted API endpoint.
        """
