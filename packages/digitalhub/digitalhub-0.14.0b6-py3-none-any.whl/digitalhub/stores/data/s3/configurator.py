# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from botocore.config import Config

from digitalhub.stores.client.dhcore.utils import refresh_token
from digitalhub.stores.credentials.configurator import Configurator
from digitalhub.stores.credentials.enums import CredsEnvVar


class S3StoreConfigurator(Configurator):
    """
    Configure the store by getting the credentials from user
    provided config or from environment.
    """

    keys = [
        CredsEnvVar.S3_ENDPOINT_URL.value,
        CredsEnvVar.S3_ACCESS_KEY_ID.value,
        CredsEnvVar.S3_SECRET_ACCESS_KEY.value,
        CredsEnvVar.S3_REGION.value,
        CredsEnvVar.S3_SIGNATURE_VERSION.value,
        CredsEnvVar.S3_SESSION_TOKEN.value,
        CredsEnvVar.S3_PATH_STYLE.value,
        CredsEnvVar.S3_CREDENTIALS_EXPIRATION.value,
    ]
    required_keys = [
        CredsEnvVar.S3_ENDPOINT_URL.value,
        CredsEnvVar.S3_ACCESS_KEY_ID.value,
        CredsEnvVar.S3_SECRET_ACCESS_KEY.value,
    ]

    def __init__(self):
        super().__init__()
        self.load_configs()

    ##############################
    # Configuration methods
    ##############################

    def load_env_vars(self) -> None:
        """
        Loads the credentials from the environment variables.
        """
        env_creds = self._creds_handler.load_from_env(self.keys)
        self._creds_handler.set_credentials(self._env, env_creds)

    def load_file_vars(self) -> None:
        """
        Loads the credentials from a file.
        """
        file_creds = self._creds_handler.load_from_file(self.keys)
        self._creds_handler.set_credentials(self._file, file_creds)

    def get_client_config(self) -> dict:
        """
        Gets S3 credentials (access key, secret key, session token, and other config).

        Returns
        -------
        dict
            Dictionary containing S3 credentials and configuration.
        """
        creds = self.evaluate_credentials()
        return self.get_creds_dict(creds)

    def get_creds_dict(self, creds: dict) -> dict:
        """
        Returns a dictionary containing the S3 credentials.

        Parameters
        ----------
        creds : dict
            The credentials dictionary.

        Returns
        -------
        dict
            A dictionary containing the S3 credentials.
        """
        return {
            "endpoint_url": creds[CredsEnvVar.S3_ENDPOINT_URL.value],
            "aws_access_key_id": creds[CredsEnvVar.S3_ACCESS_KEY_ID.value],
            "aws_secret_access_key": creds[CredsEnvVar.S3_SECRET_ACCESS_KEY.value],
            "aws_session_token": creds[CredsEnvVar.S3_SESSION_TOKEN.value],
            "config": Config(
                region_name=creds[CredsEnvVar.S3_REGION.value],
                signature_version=creds[CredsEnvVar.S3_SIGNATURE_VERSION.value],
            ),
        }

    def evaluate_credentials(self) -> dict:
        """
        Evaluates and returns the current valid credentials.
        If the credentials are expired and were loaded from file,
        it refreshes them.

        Returns
        -------
        dict
            The current valid credentials.
        """
        creds = self.get_credentials(self._origin)
        expired = creds[CredsEnvVar.S3_CREDENTIALS_EXPIRATION.value]
        if self._origin == self._file and self._is_expired(expired):
            refresh_token()
            self.load_file_vars()
            creds = self.get_credentials(self._origin)
        return creds

    def get_file_config(self) -> dict:
        """
        Returns the credentials loaded from file.

        Returns
        -------
        dict
            The credentials loaded from file.
        """
        creds = self.get_credentials(self._file)
        return self.get_creds_dict(creds)

    def get_env_config(self) -> dict:
        """
        Returns the credentials loaded from environment variables.

        Returns
        -------
        dict
            The credentials loaded from environment variables.
        """
        creds = self.get_credentials(self._env)
        return self.get_creds_dict(creds)

    @staticmethod
    def _is_expired(timestamp: str | None) -> bool:
        """
        Determines whether a given timestamp is after the current UTC time.

        Parameters
        ----------
        timestamp : str or None
            Timestamp string in the format 'YYYY-MM-DDTHH:MM:SSZ'.

        Returns
        -------
        bool
            True if the given timestamp is later than the current UTC time,
            otherwise False.
        """
        if timestamp is None:
            return False
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc) + timedelta(seconds=120)
        return dt < now
