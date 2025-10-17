# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from requests import request

from digitalhub.stores.client.dhcore.enums import AuthType
from digitalhub.stores.credentials.configurator import Configurator
from digitalhub.stores.credentials.enums import CredsEnvVar
from digitalhub.stores.credentials.handler import creds_handler
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.generic_utils import list_enum
from digitalhub.utils.uri_utils import has_remote_scheme

if typing.TYPE_CHECKING:
    from requests import Response


class ClientDHCoreConfigurator(Configurator):
    """
    DHCore client configurator for credential management and authentication.

    Handles loading credentials from environment variables and configuration files,
    evaluates authentication types, and manages token refresh operations. Supports
    multiple authentication methods: EXCHANGE (personal access token), OAUTH2
    (access + refresh tokens), ACCESS_TOKEN (access token only), and BASIC
    (username + password).

    The configurator automatically determines the best authentication method and
    handles token exchange for personal access tokens by switching to file-based
    credential storage.
    """

    keys = [*list_enum(CredsEnvVar)]
    required_keys = [CredsEnvVar.DHCORE_ENDPOINT.value]
    keys_to_prefix = [
        CredsEnvVar.DHCORE_REFRESH_TOKEN.value,
        CredsEnvVar.DHCORE_ACCESS_TOKEN.value,
        CredsEnvVar.DHCORE_ISSUER.value,
        CredsEnvVar.DHCORE_CLIENT_ID.value,
    ]

    def __init__(self) -> None:
        """
        Initialize DHCore configurator and evaluate authentication type.
        """
        super().__init__()
        self._auth_type: str | None = None
        self.set_auth_type()

    ##############################
    # Credentials methods
    ##############################

    def load_env_vars(self) -> None:
        """
        Load and sanitize credentials from environment variables.

        Sanitizes endpoint and issuer URLs to ensure proper HTTP/HTTPS schemes
        and removes trailing slashes.
        """
        env_creds = self._creds_handler.load_from_env(self.keys)
        env_creds = self._sanitize_env_vars(env_creds)
        self._creds_handler.set_credentials(self._env, env_creds)

    def _sanitize_env_vars(self, creds: dict) -> dict:
        """
        Sanitize environment variable credentials.

        Validates and normalizes endpoint and issuer URLs. Environment variables
        use full "DHCORE_" prefixes.

        Parameters
        ----------
        creds : dict
            Raw credentials from environment variables.

        Returns
        -------
        dict
            Sanitized credentials with normalized URLs.

        Raises
        ------
        ClientError
            If endpoint or issuer URLs have invalid schemes.
        """
        creds[CredsEnvVar.DHCORE_ENDPOINT.value] = self._sanitize_endpoint(creds[CredsEnvVar.DHCORE_ENDPOINT.value])
        creds[CredsEnvVar.DHCORE_ISSUER.value] = self._sanitize_endpoint(creds[CredsEnvVar.DHCORE_ISSUER.value])
        return creds

    def load_file_vars(self) -> None:
        """
        Load credentials from configuration file with CLI compatibility.

        Handles keys without "DHCORE_" prefix for CLI compatibility. Falls back
        to environment variables for missing endpoint and personal access token values.
        """
        file_creds = self._creds_handler.load_from_file(self.keys)

        # Because in the response there is no personal access token
        pat = CredsEnvVar.DHCORE_PERSONAL_ACCESS_TOKEN.value
        if file_creds[pat] is None:
            file_creds[pat] = self._creds_handler.load_from_env([pat]).get(pat)

        # Because in the response there is no endpoint
        endpoint = CredsEnvVar.DHCORE_ENDPOINT.value
        if file_creds[endpoint] is None:
            file_creds[endpoint] = self._creds_handler.load_from_env([endpoint]).get(endpoint)

        file_creds = self._sanitize_file_vars(file_creds)
        self._creds_handler.set_credentials(self._file, file_creds)

    def _sanitize_file_vars(self, creds: dict) -> dict:
        """
        Sanitize configuration file credentials.

        Handles different key formats between file and environment variables.
        File format omits "DHCORE_" prefix for: issuer, client_id, access_token,
        refresh_token. Full names used for: endpoint, user, password, personal_access_token.

        Parameters
        ----------
        creds : dict
            Raw credentials from configuration file.

        Returns
        -------
        dict
            Sanitized credentials with standardized keys and normalized URLs.

        Raises
        ------
        ClientError
            If endpoint or issuer URLs have invalid schemes.
        """
        creds[CredsEnvVar.DHCORE_ENDPOINT.value] = self._sanitize_endpoint(creds[CredsEnvVar.DHCORE_ENDPOINT.value])
        creds[CredsEnvVar.DHCORE_ISSUER.value] = self._sanitize_endpoint(creds[CredsEnvVar.DHCORE_ISSUER.value])
        return {k: v for k, v in creds.items() if k in self.keys}

    @staticmethod
    def _sanitize_endpoint(endpoint: str | None = None) -> str | None:
        """
        Validate and normalize endpoint URL.

        Ensures proper HTTP/HTTPS scheme, trims whitespace, and removes trailing slashes.

        Parameters
        ----------
        endpoint : str
            Endpoint URL to sanitize.

        Returns
        -------
        str or None
            Sanitized URL or None if input was None.

        Raises
        ------
        ClientError
            If endpoint lacks http:// or https:// scheme.
        """
        if endpoint is None:
            return
        if not has_remote_scheme(endpoint):
            raise ClientError("Invalid endpoint scheme. Must start with http:// or https://.")

        endpoint = endpoint.strip()
        return endpoint.removesuffix("/")

    def get_endpoint(self) -> str:
        """
        Get the configured DHCore backend endpoint.

        Returns the sanitized and validated endpoint URL from current credential source.

        Returns
        -------
        str
            DHCore backend endpoint URL.

        Raises
        ------
        KeyError
            If endpoint not configured in current credential source.
        """
        creds = self._creds_handler.get_credentials(self._origin)
        return creds[CredsEnvVar.DHCORE_ENDPOINT.value]

    ##############################
    # Origin methods
    ##############################

    def change_origin(self) -> None:
        """
        Switch credential source and re-evaluate authentication type.

        Changes between environment and file credential sources, then re-evaluates
        authentication type based on the new credentials.
        """
        super().change_origin()

        # Re-evaluate the auth type
        self.set_auth_type()

    ##############################
    # Auth methods
    ##############################

    def set_auth_type(self) -> None:
        """
        Determine authentication type from available credentials.

        Evaluates credentials in priority order: EXCHANGE (personal access token),
        OAUTH2 (access + refresh tokens), ACCESS_TOKEN (access only), BASIC
        (username + password). For EXCHANGE type, automatically exchanges the
        personal access token and switches to file-based credentials storage.
        """
        creds = creds_handler.get_credentials(self._origin)
        self._auth_type = self._eval_auth_type(creds)
        # If we have an exchange token, we need to get a new access token.
        # Therefore, we change the origin to file, where the refresh token is written.
        # We also try to fetch the PAT from both env and file
        if self._auth_type == AuthType.EXCHANGE.value:
            self.refresh_credentials(change_origin=True)
            # Just to ensure we get the right source from file
            self.change_to_file()

    def refreshable_auth_types(self) -> bool:
        """
        Check if current authentication supports token refresh.

        Returns True for OAUTH2 (refresh token) and EXCHANGE (personal access token),
        False for BASIC and ACCESS_TOKEN.

        Returns
        -------
        bool
            Whether authentication type supports refresh.
        """
        return self._auth_type in [AuthType.OAUTH2.value, AuthType.EXCHANGE.value]

    def get_auth_parameters(self, kwargs: dict) -> dict:
        """
        Add authentication headers/parameters to HTTP request kwargs.

        Adds Authorization Bearer header for token-based auth or auth tuple
        for basic authentication.

        Parameters
        ----------
        kwargs : dict
            HTTP request arguments to modify.

        Returns
        -------
        dict
            Modified kwargs with authentication parameters.
        """
        creds = creds_handler.get_credentials(self._origin)
        if self._auth_type in (
            AuthType.EXCHANGE.value,
            AuthType.OAUTH2.value,
            AuthType.ACCESS_TOKEN.value,
        ):
            access_token = creds[CredsEnvVar.DHCORE_ACCESS_TOKEN.value]
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {access_token}"
        elif self._auth_type == AuthType.BASIC.value:
            user = creds[CredsEnvVar.DHCORE_USER.value]
            password = creds[CredsEnvVar.DHCORE_PASSWORD.value]
            kwargs["auth"] = (user, password)
        return kwargs

    def refresh_credentials(self, change_origin: bool = False) -> None:
        """
        Refresh authentication tokens using OAuth2 flows.

        Uses refresh_token grant for OAUTH2 or token exchange for EXCHANGE authentication.
        On 400/401/403 errors with change_origin=True, attempts to switch credential
        sources and retry. Saves new credentials to configuration file.

        Parameters
        ----------
        change_origin : bool, default False
            Whether to switch credential sources on auth failure.

        Raises
        ------
        ClientError
            If auth type doesn't support refresh or credentials missing.
        """
        if not self.refreshable_auth_types():
            raise ClientError(f"Auth type {self._auth_type} does not support refresh.")

        # Get refresh endpoint
        url = self._get_refresh_endpoint()

        # Get credentials
        creds = self._creds_handler.get_credentials(self._origin)

        # Get client id
        if (client_id := creds.get(CredsEnvVar.DHCORE_CLIENT_ID.value)) is None:
            raise ClientError("Client id not set.")

        # Handling of token exchange or refresh
        if self._auth_type == AuthType.OAUTH2.value:
            response = self._call_refresh_endpoint(
                url,
                client_id=client_id,
                refresh_token=creds.get(CredsEnvVar.DHCORE_REFRESH_TOKEN.value),
                grant_type="refresh_token",
                scope="credentials",
            )
        elif self._auth_type == AuthType.EXCHANGE.value:
            response = self._call_refresh_endpoint(
                url,
                client_id=client_id,
                subject_token=creds.get(CredsEnvVar.DHCORE_PERSONAL_ACCESS_TOKEN.value),
                subject_token_type="urn:ietf:params:oauth:token-type:pat",
                grant_type="urn:ietf:params:oauth:grant-type:token-exchange",
                scope="credentials",
            )

        # Change origin of creds if needed
        if response.status_code in (400, 401, 403):
            if not change_origin:
                raise ClientError("Unable to refresh credentials. Please check your credentials.")
            self.eval_change_origin()
            self.refresh_credentials(change_origin=False)

        response.raise_for_status()

        # Read new credentials and propagate to config file
        self._export_new_creds(response.json())

    def _get_refresh_endpoint(self) -> str:
        """
        Discover OAuth2 token endpoint from issuer well-known configuration.

        Queries /.well-known/openid-configuration to extract token_endpoint for
        credential refresh operations.

        Returns
        -------
        str
            Token endpoint URL for credential refresh.

        Raises
        ------
        ClientError
            If issuer endpoint not configured.
        HTTPError
            If well-known configuration endpoint inaccessible.
        KeyError
            If token_endpoint not found in issuer configuration.
        """
        # Get issuer endpoint
        creds = self._creds_handler.get_credentials(self._origin)
        endpoint_issuer = creds.get(CredsEnvVar.DHCORE_ISSUER.value)
        if endpoint_issuer is None:
            raise ClientError("Issuer endpoint not set.")

        # Standard issuer endpoint path
        url = endpoint_issuer + "/.well-known/openid-configuration"

        # Call issuer to get refresh endpoint
        r = request("GET", url, timeout=60)
        r.raise_for_status()
        return r.json().get("token_endpoint")

    def _call_refresh_endpoint(
        self,
        url: str,
        **kwargs,
    ) -> Response:
        """
        Make OAuth2 token refresh request.

        Sends POST request with form-encoded payload using required OAuth2
        content type and 60-second timeout.

        Parameters
        ----------
        url : str
            Token endpoint URL.
        **kwargs : dict
            Token request parameters (grant_type, client_id, etc.).

        Returns
        -------
        Response
            Raw HTTP response for caller handling.
        """
        # Send request to get new access token
        payload = {**kwargs}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return request("POST", url, data=payload, headers=headers, timeout=60)

    def _eval_auth_type(self, creds: dict) -> str | None:
        """
        Determine authentication type from available credentials.

        Evaluates in priority order: EXCHANGE (personal access token), OAUTH2
        (access + refresh tokens), ACCESS_TOKEN (access only), BASIC (username + password).

        Parameters
        ----------
        creds : dict
            Available credential values.

        Returns
        -------
        str or None
            Authentication type from AuthType enum, or None if no valid credentials.
        """
        if creds[CredsEnvVar.DHCORE_PERSONAL_ACCESS_TOKEN.value] is not None:
            return AuthType.EXCHANGE.value
        if (
            creds[CredsEnvVar.DHCORE_ACCESS_TOKEN.value] is not None
            and creds[CredsEnvVar.DHCORE_REFRESH_TOKEN.value] is not None
        ):
            return AuthType.OAUTH2.value
        if creds[CredsEnvVar.DHCORE_ACCESS_TOKEN.value] is not None:
            return AuthType.ACCESS_TOKEN.value
        if creds[CredsEnvVar.DHCORE_USER.value] is not None and creds[CredsEnvVar.DHCORE_PASSWORD.value] is not None:
            return AuthType.BASIC.value
        return None

    def _export_new_creds(self, response: dict) -> None:
        """
        Save refreshed credentials and switch to file-based storage.

        Persists new tokens (access_token, refresh_token, etc.) to configuration
        file and switches credential origin to file storage.

        Parameters
        ----------
        response : dict
            OAuth2 token response with new credentials.
        """
        for key in self.keys_to_prefix:
            key = key.lower()
            if key.removeprefix("dhcore_") in response:
                response[key] = response.pop(key.removeprefix("dhcore_"))
        creds_handler.write_env(response)
        self.load_file_vars()

        # Change current origin to file because of refresh
        self.change_to_file()
