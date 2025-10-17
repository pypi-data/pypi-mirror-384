# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from requests import request

from digitalhub.stores.client.dhcore.configurator import ClientDHCoreConfigurator
from digitalhub.stores.client.dhcore.response_processor import ResponseProcessor
from digitalhub.utils.exceptions import BackendError

# Default timeout for requests (in seconds)
DEFAULT_TIMEOUT = 60


class HttpRequestHandler:
    """
    Handles HTTP request execution for DHCore client.

    Encapsulates all HTTP communication logic including request execution,
    automatic token refresh on authentication failures, and response processing.
    Works in coordination with configurator for authentication and response
    processor for parsing.
    """

    def __init__(self) -> None:
        self._configurator = ClientDHCoreConfigurator()
        self._response_processor = ResponseProcessor()

    def prepare_request(self, method: str, api: str, **kwargs) -> dict:
        """
        Execute API call with full URL construction and authentication.

        Parameters
        ----------
        method : str
            HTTP method type (GET, POST, PUT, DELETE, etc.).
        api : str
            API endpoint path to call.
        **kwargs : dict
            Additional HTTP request arguments.

        Returns
        -------
        dict
            Response from the API call.
        """
        full_kwargs = self._set_auth(**kwargs)
        url = self._build_url(api)
        return self._execute_request(method, url, **full_kwargs)

    def _execute_request(
        self,
        method: str,
        url: str,
        refresh: bool = True,
        **kwargs,
    ) -> dict:
        """
        Execute HTTP request with automatic handling.

        Sends HTTP request with authentication, handles token refresh on 401 errors,
        validates API version compatibility, and parses response. Uses 60-second
        timeout by default.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, PUT, DELETE, etc.).
        url : str
            Complete URL to request.
        refresh : bool, default True
            Whether to attempt token refresh on authentication errors.
            Set to False during refresh to prevent infinite recursion.
        **kwargs : dict
            Additional HTTP request arguments (headers, params, data, etc.).

        Returns
        -------
        dict
            Parsed response body as dictionary.
        """
        # Execute HTTP request
        response = request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)

        # Process response (version check, error parsing, dictify)
        try:
            return self._response_processor.process(response)
        except BackendError as e:
            # Handle authentication errors with token refresh
            if response.status_code == 401 and refresh and self._configurator.refreshable_auth_types():
                self._configurator.refresh_credentials(change_origin=True)
                kwargs = self._configurator.get_auth_parameters(kwargs)
                return self._execute_request(method, url, refresh=False, **kwargs)
            raise e

    def _set_auth(self, **kwargs) -> dict:
        """
        Prepare kwargs with authentication parameters.

        Parameters
        ----------
        **kwargs : dict
            Request parameters to augment with authentication.

        Returns
        -------
        dict
            kwargs enhanced with authentication parameters.
        """
        self._configurator.check_config()
        return self._configurator.get_auth_parameters(kwargs)

    def _build_url(self, api: str) -> str:
        """
        Build complete URL for API call.

        Combines configured endpoint with API path, automatically removing
        leading slashes for proper URL construction.

        Parameters
        ----------
        api : str
            API endpoint path. Leading slashes are automatically handled.

        Returns
        -------
        str
            Complete URL for the API call.
        """
        endpoint = self._configurator.get_endpoint()
        return f"{endpoint}/{api.removeprefix('/')}"
