# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.credentials.configurator import Configurator
from digitalhub.stores.credentials.enums import CredsEnvVar


class SqlStoreConfigurator(Configurator):
    """
    SQL store configuration manager for database connections.

    Handles credential management and configuration for SQL database
    connections. Loads credentials from environment variables or
    configuration files and provides connection string generation
    for database access.

    Attributes
    ----------
    keys : list[str]
        List of all supported credential keys for SQL connections.
    required_keys : list[str]
        List of mandatory credential keys that must be provided.
    """

    keys = [
        CredsEnvVar.DB_USERNAME.value,
        CredsEnvVar.DB_PASSWORD.value,
        CredsEnvVar.DB_HOST.value,
        CredsEnvVar.DB_PORT.value,
        CredsEnvVar.DB_DATABASE.value,
        CredsEnvVar.DB_PLATFORM.value,
    ]
    required_keys = [
        CredsEnvVar.DB_USERNAME.value,
        CredsEnvVar.DB_PASSWORD.value,
        CredsEnvVar.DB_HOST.value,
        CredsEnvVar.DB_PORT.value,
        CredsEnvVar.DB_DATABASE.value,
    ]

    def __init__(self):
        super().__init__()
        self.load_configs()

    ##############################
    # Configuration methods
    ##############################

    def load_env_vars(self) -> None:
        """
        Load database credentials from environment variables.

        Retrieves SQL database connection credentials from the system
        environment variables and stores them in the configurator's
        credential handler for use in database connections.
        """
        env_creds = self._creds_handler.load_from_env(self.keys)
        self._creds_handler.set_credentials(self._env, env_creds)

    def load_file_vars(self) -> None:
        """
        Load database credentials from configuration file.

        Retrieves SQL database connection credentials from a
        configuration file and stores them in the configurator's
        credential handler for use in database connections.
        """
        file_creds = self._creds_handler.load_from_file(self.keys)
        self._creds_handler.set_credentials(self._file, file_creds)

    def get_sql_conn_string(self) -> str:
        """
        Generate PostgreSQL connection string from stored credentials.

        Constructs a PostgreSQL connection string using the configured
        database credentials including username, password, host, port,
        and database name.

        Returns
        -------
        str
            A PostgreSQL connection string in the format:
            'postgresql://username:password@host:port/database'
        """
        creds = self.get_sql_credentials()
        user = creds[CredsEnvVar.DB_USERNAME.value]
        password = creds[CredsEnvVar.DB_PASSWORD.value]
        host = creds[CredsEnvVar.DB_HOST.value]
        port = creds[CredsEnvVar.DB_PORT.value]
        database = creds[CredsEnvVar.DB_DATABASE.value]
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def get_sql_credentials(self) -> dict:
        """
        Get all configured database credentials as a dictionary.

        Retrieves all available database credentials from the configured
        source and returns them as a dictionary with all credential keys
        from self.keys mapped to their values.

        Returns
        -------
        dict
            Dictionary containing all credential key-value pairs from self.keys.
            Keys correspond to database connection parameters such as
            username, password, host, port, database, and platform.
        """
        creds = self.get_credentials(self._origin)
        return {key: creds.get(key) for key in self.keys}
