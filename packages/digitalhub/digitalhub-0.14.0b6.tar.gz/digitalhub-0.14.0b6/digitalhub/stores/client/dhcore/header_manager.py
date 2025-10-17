# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class HeaderManager:
    """
    Manages HTTP headers for DHCore client requests.

    Provides utilities for setting and managing common HTTP headers
    like Content-Type for JSON requests.
    """

    @staticmethod
    def ensure_headers(**kwargs) -> dict:
        """
        Initialize headers dictionary in kwargs.

        Ensures parameter dictionary has 'headers' key for HTTP headers,
        guaranteeing consistent structure for all parameter building methods.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Dictionary with guaranteed 'headers' key containing
            empty dict if not already present.
        """
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        return kwargs

    @staticmethod
    def set_json_content_type(**kwargs) -> dict:
        """
        Set Content-Type header to application/json.

        Ensures that the 'Content-Type' header is set to 'application/json'
        for requests that require JSON payloads.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Dictionary with 'Content-Type' header set to 'application/json'.
        """
        kwargs = HeaderManager.ensure_headers(**kwargs)
        kwargs["headers"]["Content-Type"] = "application/json"
        return kwargs
