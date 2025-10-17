# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from digitalhub.stores.data._base.store import Store
from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.types import SourcesOrListOfSources


class RemoteStore(Store):
    """
    HTTP store class. It implements the Store interface and provides methods to fetch
    artifacts from remote HTTP based storage.
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
        # Handle destination
        if dst is None:
            dst = self._build_temp()
        else:
            self._check_local_dst(str(dst))

        if dst.suffix == "":
            dst = dst / "data.file"

        self._check_overwrite(dst, overwrite)
        self._build_path(dst)

        return self._download_file(root, dst, overwrite)

    def upload(self, src: SourcesOrListOfSources, dst: str) -> list[tuple[str, str]]:
        """
        Upload an artifact to storage.

        Raises
        ------
        StoreError
            This method is not implemented.
        """
        raise StoreError("Remote HTTP store does not support upload.")

    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Get file information from HTTP(s) storage.

        Parameters
        ----------
        paths : list[str]
            List of source paths.

        Returns
        -------
        list[dict]
            Returns files metadata.
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
        extension = self._head_extension(path, file_format)
        return reader.read_df(path, extension, **kwargs)

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
        raise StoreError("Remote store does not support query.")

    def write_df(self, df: Any, dst: str, extension: str | None = None, **kwargs) -> str:
        """
        Method to write a dataframe to a file. Note that this method is not implemented
        since the remote store is not meant to write dataframes.

        Raises
        ------
        NotImplementedError
            This method is not implemented.
        """
        raise NotImplementedError("Remote store does not support write_df.")

    ##############################
    # Helper methods
    ##############################

    @staticmethod
    def _check_head(src) -> None:
        """
        Check if the source exists.

        Parameters
        ----------
        src : str
            The source location.

        Raises
        ------
        HTTPError
            If an error occurs while checking the source.
        """
        r = requests.head(src, timeout=60)
        r.raise_for_status()

    def _download_file(self, url: str, dst: Path, overwrite: bool) -> str:
        """
        Method to download a file from a given url.

        Parameters
        ----------
        url : str
            The url of the file to download.
        dst : Path
            The destination of the file.
        overwrite : bool
            Whether to overwrite existing files.

        Returns
        -------
        str
            The path of the downloaded file.
        """
        self._check_head(url)
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dst, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return str(dst)

    def _head_extension(self, url: str, file_format: str | None = None) -> str:
        """
        Method to get the extension of a file from a given url.

        Parameters
        ----------
        url : str
            The url of the file to get the extension.
        file_format : str
            The file format to check.

        Returns
        -------
        str
            File extension.
        """
        if file_format is not None:
            return file_format
        try:
            r = requests.head(url, timeout=60)
            r.raise_for_status()
            content_type = r.headers["content-type"]
            if "text" in content_type:
                return "csv"
            else:
                raise ValueError("Content type not supported.")
        except Exception as e:
            raise e
