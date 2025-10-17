# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

from digitalhub.stores.readers.data.api import get_reader_by_engine
from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.types import SourcesOrListOfSources
from digitalhub.utils.uri_utils import has_local_scheme

if typing.TYPE_CHECKING:
    from digitalhub.stores.credentials.configurator import Configurator
    from digitalhub.stores.readers.data._base.reader import DataframeReader


class Store:
    """
    Store abstract class.
    """

    def __init__(self, configurator: Configurator | None = None) -> None:
        self._configurator = configurator

    ##############################
    # I/O methods
    ##############################

    @abstractmethod
    def download(
        self,
        src: str,
        dst: Path,
        overwrite: bool = False,
    ) -> str:
        """
        Method to download material entity from storage.
        """

    @abstractmethod
    def upload(
        self,
        src: SourcesOrListOfSources,
        dst: str,
    ) -> list[tuple[str, str]]:
        """
        Method to upload material entity to storage.
        """

    @abstractmethod
    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Method to get file metadata.
        """

    ##############################
    # Datastore methods
    ##############################

    @abstractmethod
    def read_df(
        self,
        path: SourcesOrListOfSources,
        file_format: str | None = None,
        engine: str | None = None,
        **kwargs,
    ) -> Any:
        """
        Read DataFrame from path.
        """

    @abstractmethod
    def query(
        self,
        query: str,
        engine: str | None = None,
    ) -> Any:
        """
        Query data from database.
        """

    @abstractmethod
    def write_df(
        self,
        df: Any,
        dst: str,
        extension: str | None = None,
        **kwargs,
    ) -> str:
        """
        Write DataFrame as parquet or csv.
        """

    ##############################
    # Helpers methods
    ##############################

    def _check_local_src(self, src: str) -> None:
        """
        Check if the source path is local.

        Parameters
        ----------
        src : str
            The source path.

        Raises
        ------
        StoreError
            If the source is not a local path.
        """
        if not has_local_scheme(src):
            raise StoreError(f"Source '{src}' is not a local path.")

    def _check_local_dst(self, dst: str) -> None:
        """
        Check if the destination path is local.

        Parameters
        ----------
        dst : str
            The destination path.

        Raises
        ------
        StoreError
            If the destination is not a local path.
        """
        if not has_local_scheme(dst):
            raise StoreError(f"Destination '{dst}' is not a local path.")

    def _check_overwrite(self, dst: Path, overwrite: bool) -> None:
        """
        Check if destination path exists for overwrite.

        Parameters
        ----------
        dst : Path
            Destination path as filename.
        overwrite : bool
            Specify if overwrite an existing file.

        Raises
        ------
        StoreError
            If destination path exists and overwrite is False.
        """
        if dst.exists() and not overwrite:
            raise StoreError(f"Destination {str(dst)} already exists.")

    @staticmethod
    def _build_path(path: str | Path) -> None:
        """
        Get path from store path and path.

        Parameters
        ----------
        path : str | Path
            The path to build.
        """
        if not isinstance(path, Path):
            path = Path(path)
        # If the path does not exist, we need to infer if it's a file or directory
        if path.suffix and not path.name.startswith("."):
            # Looks like a file, use parent
            dir_path = path.parent
        else:
            # Looks like a directory (even if it contains dots)
            dir_path = path
        dir_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _build_temp() -> Path:
        """
        Build a temporary path.

        Returns
        -------
        Path
            Temporary path.
        """
        tmpdir = mkdtemp()
        return Path(tmpdir)

    @staticmethod
    def _get_reader(engine: str | None = None) -> DataframeReader:
        """
        Get Dataframe reader.

        Parameters
        ----------
        engine : str
            Dataframe engine (pandas, polars, etc.).

        Returns
        -------
        Any
            Reader object.
        """
        return get_reader_by_engine(engine)

    @staticmethod
    def _get_extension(extension: str | None = None, path: str | None = None) -> str:
        """
        Get extension from path.

        Parameters
        ----------
        extension : str
            The extension to get.
        path : str
            The path to get the extension from.

        Returns
        -------
        str
            The extension.
        """
        if extension is not None:
            return extension
        if path is not None:
            return Path(path).suffix.removeprefix(".")
        raise ValueError("Extension or path must be provided.")
