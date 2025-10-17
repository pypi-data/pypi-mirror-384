# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from digitalhub.stores.data._base.store import Store
from digitalhub.stores.readers.data.api import get_reader_by_object
from digitalhub.utils.exceptions import ConfigError, StoreError
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from sqlalchemy.engine.row import Row

    from digitalhub.stores.credentials.configurator import Configurator
    from digitalhub.stores.data.sql.configurator import SqlStoreConfigurator


class SqlStore(Store):
    """
    SQL-based data store implementation for database operations.

    Provides functionality for reading, writing, and managing data in SQL
    databases. Implements the Store interface with SQL-specific operations
    including table downloads, DataFrame operations, and query execution.

    Attributes
    ----------
    _configurator : SqlStoreConfigurator
        The configurator instance for managing SQL database credentials
        and connection parameters.
    """

    def __init__(self, configurator: Configurator | None = None) -> None:
        super().__init__(configurator)
        self._configurator: SqlStoreConfigurator

    ##############################
    # I/O methods
    ##############################

    def download(
        self,
        src: str,
        dst: Path,
        overwrite: bool = False,
    ) -> str:
        """
        Download a SQL table as a Parquet file to local storage.

        Retrieves data from a SQL table and saves it as a Parquet file
        at the specified destination. The source path should be in the
        format 'sql://database/schema/table'.

        Parameters
        ----------
        src : str
            The SQL URI path of the table to download in the format
            'sql://database/schema/table' or 'sql://database/table'.
        dst : Path
            The destination path on the local filesystem where the
            Parquet file will be saved.
        overwrite : bool, default False
            Whether to overwrite existing files at the destination path.

        Returns
        -------
        str
            The absolute path of the downloaded Parquet file.

        Raises
        ------
        StoreError
            If the destination path has an invalid extension or if
            file operations fail.
        """
        table_name = self._get_table_name(src) + ".parquet"
        # Case where dst is not provided
        if dst is None:
            dst = Path(self._build_temp("sql")) / table_name
        else:
            self._check_local_dst(str(dst))
            path = Path(dst)

            # Case where dst is a directory
            if path.suffix == "":
                dst = path / table_name

            # Case where dst is a file
            elif path.suffix != ".parquet":
                raise StoreError("The destination path must be a directory or a parquet file.")

            self._check_overwrite(dst, overwrite)
            self._build_path(dst)

        schema = self._get_schema(src)
        table = self._get_table_name(src)
        return self._download_table(schema, table, str(dst))

    def upload(
        self,
        src: SourcesOrListOfSources,
        dst: str,
    ) -> list[tuple[str, str]]:
        """
        Upload artifacts to SQL storage.

        Raises
        ------
        StoreError
            Always raised as SQL store does not support direct upload.
        """
        raise StoreError("SQL store does not support upload.")

    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Get file metadata information from SQL storage.

        Returns
        -------
        list[dict]
            Empty list.
        """
        return []

    ##############################
    # Datastore methods
    ##############################

    def read_df(
        self,
        path: SourcesOrListOfSources,
        file_format: str | None = None,
        engine: str | None = None,
        **kwargs,
    ) -> Any:
        """
        Read a DataFrame from a SQL table.

        Connects to the SQL database and reads data from the specified
        table into a DataFrame using the specified engine (pandas, polars, etc.).

        Parameters
        ----------
        path : SourcesOrListOfSources
            The SQL URI path to read from in the format
            'sql://database/schema/table'. Only single paths are supported.
        file_format : str
            File format specification (not used for SQL operations).
        engine : str
            DataFrame engine to use (e.g., 'pandas', 'polars').
            If None, uses the default engine.
        **kwargs : dict
            Additional keyword arguments passed to the reader.

        Returns
        -------
        Any
            DataFrame object containing the table data.

        Raises
        ------
        StoreError
            If a list of paths is provided (only single path supported).
        """
        if isinstance(path, list):
            raise StoreError("SQL store can only read a single DataFrame at a time.")

        reader = self._get_reader(engine)
        schema = self._get_schema(path)
        table = self._get_table_name(path)
        sql_engine = self._check_factory(schema=schema)

        sa_table = Table(table, MetaData(), autoload_with=sql_engine)
        stm = select(sa_table)

        return reader.read_table(stm, sql_engine, **kwargs)

    def query(
        self,
        query: str,
        path: str,
        engine: str | None = None,
    ) -> Any:
        """
        Execute a custom SQL query and return results as a DataFrame.

        Runs a SQL query against the database specified in the path
        and returns the results using the specified DataFrame engine.

        Parameters
        ----------
        query : str
            The SQL query string to execute against the database.
        path : str
            The SQL URI path specifying the database connection
            in the format 'sql://database/schema/table'.
        engine : str
            DataFrame engine to use for result processing
            (e.g., 'pandas', 'polars'). If None, uses the default.

        Returns
        -------
        Any
            DataFrame object containing the query results.
        """
        reader = self._get_reader(engine)
        schema = self._get_schema(path)
        sql_engine = self._check_factory(schema=schema)
        return reader.read_table(query, sql_engine)

    def write_df(self, df: Any, dst: str, extension: str | None = None, **kwargs) -> str:
        """
        Write a DataFrame to a SQL database table.

        Takes a DataFrame and writes it to the specified SQL table.
        The destination should be in SQL URI format. Additional
        parameters are passed to the underlying to_sql() method.

        Parameters
        ----------
        df : Any
            The DataFrame object to write to the database.
        dst : str
            The destination SQL URI in the format
            'sql://database/schema/table' or 'sql://database/table'.
        extension : str
            File extension parameter (not used for SQL operations).
        **kwargs : dict
            Additional keyword arguments passed to the DataFrame's
            to_sql() method for controlling write behavior.

        Returns
        -------
        str
            The SQL URI path where the DataFrame was written.
        """
        schema = self._get_schema(dst)
        table = self._get_table_name(dst)
        return self._upload_table(df, schema, table, **kwargs)

    ##############################
    # Wrapper methods
    ##############################

    def get_engine(self, schema: str | None = None) -> Engine:
        """
        Get a SQLAlchemy engine connected to the database.

        Returns
        -------
        Engine
            A SQLAlchemy engine instance connected to the database.
        """
        return self._check_factory(schema=schema)

    ##############################
    # Private I/O methods
    ##############################

    def _download_table(self, schema: str, table: str, dst: str) -> str:
        """
        Download a specific table from SQL database to Parquet file.

        Internal method that handles the actual table download process.
        Connects to the database, retrieves all data from the specified
        table, and writes it to a Parquet file using PyArrow.

        Parameters
        ----------
        schema : str
            The database schema name containing the table.
        table : str
            The name of the table to download.
        dst : str
            The local file path where the Parquet file will be saved.

        Returns
        -------
        str
            The destination file path of the created Parquet file.
        """
        engine = self._check_factory(schema=schema)

        # Read the table from the database
        sa_table = Table(table, MetaData(), autoload_with=engine)
        stm = select(sa_table)
        with engine.begin() as conn:
            result: list[Row] = conn.execute(stm).fetchall()

        # Parse the result
        data = {col: [row[idx] for row in result] for idx, col in enumerate(sa_table.columns.keys())}

        # Convert the result to a pyarrow table and
        # write the pyarrow table to a Parquet file
        arrow_table = pa.Table.from_pydict(data)
        pq.write_table(arrow_table, dst)

        engine.dispose()

        return dst

    def _upload_table(self, df: Any, schema: str, table: str, **kwargs) -> str:
        """
        Upload a DataFrame to a SQL table.

        Internal method that handles writing a DataFrame to a SQL database
        table. Uses the appropriate reader based on the DataFrame type
        and manages the database connection.

        Parameters
        ----------
        df : Any
            The DataFrame object to upload to the database.
        schema : str
            The target database schema name.
        table : str
            The target table name within the schema.
        **kwargs : dict
            Additional keyword arguments passed to the write operation,
            such as if_exists, index, method, etc.

        Returns
        -------
        str
            The SQL URI where the DataFrame was saved in the format
            'sql://database/schema/table'.
        """
        reader = get_reader_by_object(df)
        engine = self._check_factory()
        reader.write_table(df, table, engine, schema, **kwargs)
        engine.dispose()
        return f"sql://{engine.url.database}/{schema}/{table}"

    ##############################
    # Helper methods
    ##############################

    def _get_connection_string(self) -> str:
        """
        Retrieve the database connection string from the configurator.

        Gets the PostgreSQL connection string using the configured
        database credentials (username, password, host, port, database).

        Returns
        -------
        str
            The PostgreSQL connection string in the format
            'postgresql://username:password@host:port/database'.
        """
        return self._configurator.get_sql_conn_string()

    def _get_engine(self, schema: str | None = None) -> Engine:
        """
        Create a SQLAlchemy engine from the connection string.

        Establishes a database engine using the configured connection
        string with appropriate connection parameters and schema settings.

        Parameters
        ----------
        schema : str
            The database schema to set in the search path.
            If provided, sets the PostgreSQL search_path option.

        Returns
        -------
        Engine
            A configured SQLAlchemy engine instance.

        Raises
        ------
        StoreError
            If the connection string is invalid or engine creation fails.
        """
        connection_string = self._get_connection_string()
        if not isinstance(connection_string, str):
            raise StoreError("Connection string must be a string.")
        try:
            connect_args = {"connect_timeout": 30}
            if schema is not None:
                connect_args["options"] = f"-csearch_path={schema}"
            return create_engine(connection_string, connect_args=connect_args)
        except Exception as ex:
            raise StoreError(f"Something wrong with connection string. Arguments: {str(ex.args)}")

    def _check_factory(self, retry: bool = True, schema: str | None = None) -> Engine:
        """
        Validate database accessibility and return a working engine.

        Creates and tests a database engine, with retry capability if
        the initial connection fails. Handles configuration changes
        and ensures the database is accessible before returning.

        Parameters
        ----------
        retry : bool, default True
            Whether to attempt a retry with different configuration
            if the initial connection fails.
        schema : str
            The database schema to configure in the engine.

        Returns
        -------
        Engine
            A validated SQLAlchemy engine with confirmed database access.

        Raises
        ------
        ConfigError
            If database access fails and retry is exhausted or disabled.
        """
        try:
            engine = self._get_engine(schema)
            self._check_access_to_storage(engine)
            return engine
        except ConfigError as e:
            if retry:
                self._configurator.eval_change_origin()
                return self._check_factory(retry=False, schema=schema)
            raise e

    @staticmethod
    def _parse_path(path: str) -> dict:
        """
        Parse a SQL URI path into its component parts.

        Breaks down a SQL URI into database, schema, and table components.
        Supports both full three-part paths and simplified two-part paths
        (using 'public' as default schema).

        Parameters
        ----------
        path : str
            The SQL URI path to parse in the format
            'sql://database/schema/table' or 'sql://database/table'.

        Returns
        -------
        dict
            Dictionary containing parsed components with keys:
            'database', 'schema', and 'table'.

        Raises
        ------
        ValueError
            If the path format is invalid or doesn't follow the
            expected SQL URI structure.
        """
        # Parse path
        err_msg = "Invalid SQL path. Must be sql://<database>/<schema>/<table> or sql://<database>/<table>"
        protocol, pth = path.split("://")
        components = pth.split("/")
        if protocol != "sql" or not (2 <= len(components) <= 3):
            raise ValueError(err_msg)

        # Get components
        database = components[0]
        table = components[-1]
        schema = components[1] if len(components) == 3 else "public"
        return {"database": database, "schema": schema, "table": table}

    def _get_schema(self, uri: str) -> str:
        """
        Extract the schema name from a SQL URI.

        Parses the SQL URI and returns the schema component.
        Uses 'public' as the default schema if not specified in the URI.

        Parameters
        ----------
        uri : str
            The SQL URI to extract the schema from.

        Returns
        -------
        str
            The schema name extracted from the URI.
        """
        return str(self._parse_path(uri).get("schema"))

    def _get_table_name(self, uri: str) -> str:
        """
        Extract the table name from a SQL URI.

        Parses the SQL URI and returns the table component,
        which is always the last part of the URI path.

        Parameters
        ----------
        uri : str
            The SQL URI to extract the table name from.

        Returns
        -------
        str
            The table name extracted from the URI.
        """
        return str(self._parse_path(uri).get("table"))

    @staticmethod
    def _check_access_to_storage(engine: Engine) -> None:
        """
        Verify database connectivity using the provided engine.

        Tests the database connection by attempting to connect.
        Properly disposes of the engine if connection fails.

        Parameters
        ----------
        engine : Engine
            The SQLAlchemy engine to test for connectivity.

        Raises
        ------
        ConfigError
            If database connection cannot be established.
        """
        try:
            engine.connect()
        except SQLAlchemyError:
            engine.dispose()
            raise ConfigError("No access to db!")
