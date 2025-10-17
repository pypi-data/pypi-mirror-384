# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.stores.credentials.enums import CredsOrigin


class CredentialsStore:
    """
    Store and retrieve credentials for different profiles and origins.

    Attributes
    ----------
    _file_creds : dict of str to dict
        Credentials stored by profile from file origin.
    _env_creds : dict of str to Any
        Credentials stored from environment origin.
    """

    def __init__(self) -> None:
        self._file_creds: dict[str, dict[str, Any]] = {}
        self._env_creds: dict[str, Any] = {}

    def set_credentials(
        self,
        profile: str,
        origin: str,
        credentials: dict[str, Any],
    ) -> None:
        """
        Set all credentials for a given profile and origin.

        Parameters
        ----------
        profile : str
            Name of the credentials profile.
        origin : str
            Origin of the credentials ('env' or 'file').
        credentials : dict of str to Any
            Dictionary of credentials to set.
        """
        if origin == CredsOrigin.ENV.value:
            for key, value in credentials.items():
                self._env_creds[key] = value
            return
        if profile not in self._file_creds:
            self._file_creds[profile] = {}
        for key, value in credentials.items():
            self._file_creds[profile][key] = value

    def get_credentials(
        self,
        profile: str,
        origin: str,
    ) -> dict[str, Any]:
        """
        Get all credentials for a given profile and origin.

        Parameters
        ----------
        profile : str
            Name of the credentials profile.
        origin : str
            Origin of the credentials ('env' or 'file').

        Returns
        -------
        dict of str to Any
            Dictionary of credentials for the profile and origin.
        """
        if origin == CredsOrigin.ENV.value:
            return self._env_creds
        return self._file_creds[profile]
