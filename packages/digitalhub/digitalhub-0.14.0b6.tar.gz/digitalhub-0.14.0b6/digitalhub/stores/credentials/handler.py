# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os

from digitalhub.stores.credentials.enums import SetCreds
from digitalhub.stores.credentials.ini_module import (
    load_file,
    load_key,
    load_profile,
    set_current_profile,
    write_config,
)
from digitalhub.stores.credentials.store import CredentialsStore


class CredentialHandler:
    """
    Handler for configuring clients and managing credentials.

    Attributes
    ----------
    _creds_store : CredentialsStore
        Store for credentials.
    _profile : str
        Current credentials profile name.
    """

    def __init__(self) -> None:
        self._creds_store = CredentialsStore()
        self._profile = self._read_current_profile()

    @staticmethod
    def _read_current_profile() -> str:
        """
        Read the current credentials profile name.

        Returns
        -------
        str
            Name of the credentials profile.
        """
        profile = os.getenv(SetCreds.DH_PROFILE.value)
        if profile is not None:
            return profile
        file = load_file()
        profile = load_profile(file)
        if profile is not None:
            return profile
        return SetCreds.DEFAULT.value

    ##############################
    # Public methods
    ##############################

    def set_current_profile(self, creds_set: str) -> None:
        """
        Set the current credentials profile name.

        Parameters
        ----------
        creds_set : str
            Name of the credentials profile to set.
        """
        self._profile = creds_set
        set_current_profile(creds_set)

    def get_current_profile(self) -> str:
        """
        Get the current credentials profile name.

        Returns
        -------
        str
            Name of the current credentials profile.
        """
        return self._profile

    def load_from_env(self, vars: list[str]) -> dict:
        """
        Load variables from environment.

        Parameters
        ----------
        vars : list of str
            List of environment variable names to load.

        Returns
        -------
        dict
            Dictionary of environment variable values.
        """
        return {var: os.getenv(var) for var in vars}

    def load_from_file(self, vars: list[str]) -> dict:
        """
        Load variables from credentials config file.

        Parameters
        ----------
        vars : list of str
            List of variable names to load from file.

        Returns
        -------
        dict
            Dictionary of variable values from file.
        """
        file = load_file()
        profile = load_profile(file)
        if profile is not None:
            self._profile = profile
        return {var: load_key(file, self._profile, var) for var in vars}

    def write_env(self, creds: dict) -> None:
        """
        Write credentials to the .dhcore file for the current profile.

        Parameters
        ----------
        creds : dict
            Credentials to write.
        """
        write_config(creds, self._profile)

    ##############################
    # Credentials store methods
    ##############################

    def set_credentials(self, origin: str, creds: dict) -> None:
        """
        Set credentials for the current profile and origin.

        Parameters
        ----------
        origin : str
            The origin of the credentials ('env' or 'file').
        creds : dict
            Credentials to set.
        """
        self._creds_store.set_credentials(self._profile, origin, creds)

    def get_credentials(self, origin: str) -> dict:
        """
        Get credentials for the current profile from the specified origin.

        Parameters
        ----------
        origin : str
            The origin to get credentials from ('env' or 'file').

        Returns
        -------
        dict
            Dictionary of credentials.
        """
        return self._creds_store.get_credentials(self._profile, origin)


# Define global credential handler
creds_handler = CredentialHandler()
