# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

from digitalhub.stores.data._base.store import Store
from digitalhub.stores.readers.data.api import get_reader_by_object
from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.file_utils import get_file_info_from_local
from digitalhub.utils.types import SourcesOrListOfSources


class LocalStore(Store):
    """
    Local store class. It implements the Store interface and provides methods to fetch and persist
    artifacts on local filesystem based storage.
    """

    ##############################
    # I/O methods
    ##############################

    def download(
        self,
        root: str,
        dst: Path,
        overwrite: bool = False,
    ) -> str:
        """
        Download artifacts from storage.

        Parameters
        ----------
        src : str
            Path of the material entity.
        dst : str
            The destination of the material entity on local filesystem.
        overwrite : bool
            Specify if overwrite existing file(s).

        Returns
        -------
        str
            Destination path of the downloaded files.
        """
        raise StoreError("Local store does not support download.")

    def upload(self, src: SourcesOrListOfSources, dst: str) -> list[tuple[str, str]]:
        """
        Upload an artifact to storage.

        Raises
        ------
        StoreError
            This method is not implemented.
        """
        raise StoreError("Local store does not support upload.")

    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Method to get file metadata.

        Parameters
        ----------
        paths : list
            List of source paths.

        Returns
        -------
        list[dict]
            Returns files metadata.
        """
        return [get_file_info_from_local(p) for p in paths]

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
        Read DataFrame from path.

        Parameters
        ----------
        path : SourcesOrListOfSources
            Path(s) to read DataFrame from.
        file_format : str
            Extension of the file.
        engine : str
            Dataframe engine (pandas, polars, etc.).
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        Any
            DataFrame.
        """
        reader = self._get_reader(engine)

        dfs = []
        if isinstance(path, list):
            for p in path:
                file_format = self._get_extension(file_format, p)
                dfs.append(reader.read_df(p, file_format, **kwargs))
        elif Path(path).is_dir():
            import glob

            paths = glob.glob(f"{path}/*")
            for p in paths:
                file_format = self._get_extension(file_format, p)
                dfs.append(reader.read_df(p, file_format, **kwargs))
        else:
            file_format = self._get_extension(file_format, path)
            dfs.append(reader.read_df(path, file_format, **kwargs))

        if len(dfs) == 1:
            return dfs[0]

        return reader.concat_dfs(dfs)

    def query(
        self,
        query: str,
        engine: str | None = None,
    ) -> Any:
        """
        Query data from database.

        Parameters
        ----------
        query : str
            The query to execute.
        engine : str
            Dataframe engine (pandas, polars, etc.).

        Returns
        -------
        Any
            DataFrame.
        """
        raise StoreError("Local store does not support query.")

    def write_df(self, df: Any, dst: str, extension: str | None = None, **kwargs) -> str:
        """
        Method to write a dataframe to a file. Kwargs are passed to df.to_parquet().
        If destination is not provided, the dataframe is written to the default
        store path with generated name.

        Parameters
        ----------
        df : Any
            The dataframe to write.
        dst : str
            The destination of the dataframe.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        str
            Path of written dataframe.
        """
        self._check_local_dst(dst)
        reader = get_reader_by_object(df)
        reader.write_df(df, dst, extension=extension, **kwargs)
        return dst
