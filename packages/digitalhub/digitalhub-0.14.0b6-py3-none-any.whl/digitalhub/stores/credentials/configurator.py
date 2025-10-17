# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod

from digitalhub.stores.credentials.enums import CredsOrigin
from digitalhub.stores.credentials.handler import creds_handler
from digitalhub.utils.exceptions import ConfigError


class Configurator:
    """
    Base configurator for credentials management.

    Attributes
    ----------
    keys : list of str
        List of credential keys to manage.
    required_keys : list of str
        List of required credential keys.
    _env : str
        Environment origin identifier.
    _file : str
        File origin identifier.
    _creds_handler : object
        Credentials handler instance.
    """

    # Must be set in implementing class
    keys: list[str] = []
    required_keys: list[str] = []

    # Origin of the credentials
    _env = CredsOrigin.ENV.value
    _file = CredsOrigin.FILE.value

    # Credentials handler
    _creds_handler = creds_handler

    def __init__(self):
        self._current_profile = self._creds_handler.get_current_profile()
        self.load_configs()
        self._changed_origin = False
        self._origin = self.set_origin()

    ##############################
    # Configuration
    ##############################

    def load_configs(self) -> None:
        """
        Load the configuration from both environment and file sources.
        """
        self.load_env_vars()
        self.load_file_vars()

    @abstractmethod
    def load_env_vars(self) -> None: ...

    @abstractmethod
    def load_file_vars(self) -> None: ...

    def check_config(self) -> None:
        """
        Check if the current profile has changed and reload
        the file credentials if needed.
        """
        if (current := self._creds_handler.get_current_profile()) != self._current_profile:
            self.load_file_vars()
            self._current_profile = current

    def set_origin(self) -> str:
        """
        Determine the default origin for credentials (env or file).

        Returns
        -------
        str
            The selected origin ('env' or 'file').

        Raises
        ------
        ConfigError
            If required credentials are missing in both sources.
        """
        origin = self._env

        env_creds = self._creds_handler.get_credentials(self._env)
        missing_env = self._check_credentials(env_creds)

        file_creds = self._creds_handler.get_credentials(self._file)
        missing_file = self._check_credentials(file_creds)

        msg = ""
        if missing_env:
            msg = f"Missing required vars in env: {', '.join(missing_env)}"
            origin = self._file
            self._changed_origin = True
        elif missing_file:
            msg += f"Missing required vars in .dhcore.ini file: {', '.join(missing_file)}"

        if missing_env and missing_file:
            raise ConfigError(msg)

        return origin

    def eval_change_origin(self) -> None:
        """
        Attempt to change the origin of credentials.
        Raise error if already evaluated.
        """
        try:
            self.change_origin()
        except ConfigError:
            raise ConfigError("Credentials origin already evaluated. Please check your credentials.")

    def change_origin(self) -> None:
        """
        Change the origin of credentials from env to file or vice versa.
        """
        if self._changed_origin:
            raise ConfigError("Origin has already been changed.")
        if self._origin == self._env:
            self.change_to_file()
        else:
            self.change_to_env()

    def change_to_file(self) -> None:
        """
        Set the credentials origin to file.
        """
        if self._origin == self._env:
            self._changed_origin = True
        self._origin = CredsOrigin.FILE.value

    def change_to_env(self) -> None:
        """
        Set the credentials origin to environment.
        """
        if self._origin == self._file:
            self._changed_origin = True
        self._origin = CredsOrigin.ENV.value

    ##############################
    # Credentials
    ##############################

    def get_credentials(self, origin: str) -> dict:
        """
        Retrieve credentials for the specified origin.

        Parameters
        ----------
        origin : str
            The origin to retrieve credentials from ('env' or 'file').

        Returns
        -------
        dict
            Dictionary of credentials.
        """
        return self._creds_handler.get_credentials(origin)

    def _check_credentials(self, creds: dict) -> list[str]:
        """
        Check for missing required credentials in a dictionary.

        Parameters
        ----------
        creds : dict
            Dictionary of credentials to check.

        Returns
        -------
        list of str
            List of missing required credential keys.
        """
        missing_keys = []
        for k, v in creds.items():
            if v is None and k in self.required_keys:
                missing_keys.append(k)
        return missing_keys
