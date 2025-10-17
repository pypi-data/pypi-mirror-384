# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path

from digitalhub.entities._base.material.utils import refresh_decorator
from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._processors.processors import context_processor
from digitalhub.stores.data.api import get_store
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities._base.material.spec import MaterialSpec
    from digitalhub.entities._base.material.status import MaterialStatus


class MaterialEntity(VersionedEntity):
    """
    A class representing an entity that can be materialized
    as file(s).
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: MaterialSpec,
        status: MaterialStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)
        self.spec: MaterialSpec
        self.status: MaterialStatus

    def save(self, update: bool = False) -> MaterialEntity:
        """
        Save entity into backend.

        Parameters
        ----------
        update : bool
            Flag to indicate update.

        Returns
        -------
        MaterialEntity
            Entity saved.
        """
        # Evaluate files info list length
        files = None
        if self.status.files is not None and len(self.status.files) > 5 and not self._context().local:
            files = self.status.files
            self.status.files = []

        obj: MaterialEntity = super().save(update)

        # Handle files info
        if files is not None:
            context_processor.update_files_info(self.project, self.ENTITY_TYPE, self.id, files)
            self.add_files_info(files)

        return obj

    ##############################
    # I/O Methods
    ##############################

    @refresh_decorator
    def as_file(self) -> list[str]:
        """
        Get object as file(s). It downloads the object from storage in
        a temporary folder and returns the list of downloaded files paths.

        Returns
        -------
        list[str]
            List of file paths.
        """
        store = get_store(self.spec.path)
        dst = store._build_temp()
        return store.download(self.spec.path, dst=dst)

    @refresh_decorator
    def download(
        self,
        destination: str | None = None,
        overwrite: bool = False,
    ) -> str:
        """
        This function downloads one or more file from storage on local
        machine from spec.path.
        The files are downloaded into a destination folder. If the destination
        is not specified, it will set by default under the context path
        as '<ctx-root>/<entity_type>', e.g. './dataitem'.
        The overwrite flag allows to overwrite existing file(s) in the
        destination folder.

        Parameters
        ----------
        destination : str
            Destination path as filename or directory.
        overwrite : bool
            Specify if overwrite existing file(s). If file(s) already
            exist and overwrite is False, it will raise an error.

        Returns
        -------
        str
            Download path.

        Examples
        --------
        Download a single file:

        >>> path = entity.download()
        >>> print(path)
        dataitem/data.csv
        """
        store = get_store(self.spec.path)

        if destination is None:
            dst = self._context().root / self.ENTITY_TYPE
        else:
            dst = Path(destination)

        return store.download(self.spec.path, dst, overwrite=overwrite)

    @refresh_decorator
    def upload(self, source: SourcesOrListOfSources) -> None:
        """
        Upload object from given local path to spec path destination.
        Source must be a local path. If the path is a folder, destination
        path (object's spec path) must be a folder or a partition ending
        with '/' (s3).

        Parameters
        ----------
        source : str | list[str]
            Local filepath, directory or list of filepaths.

        Examples
        --------
        Upload a single file:

        >>> entity.spec.path = "s3://bucket/data.csv"
        >>> entity.upload("./data.csv")

        Upload a folder:
        >>> entity.spec.path = "s3://bucket/data/"
        >>> entity.upload("./data")
        """
        # Get store and upload object
        store = get_store(self.spec.path)
        paths = store.upload(source, self.spec.path)

        # Update files info
        files_info = store.get_file_info(self.spec.path, paths)
        self._update_files_info(files_info)

    ##############################
    #  Public Helpers
    ##############################

    def add_files_info(self, files: list[dict]) -> None:
        """
        Add a file to the status.

        Parameters
        ----------
        files : list[dict]
            Files to add.
        """
        available = 100 - len(self.status.files)
        if len(files) > available:
            files = files[:available]

        path_list = self.get_file_paths()
        for f in files:
            if f.get("path") not in path_list:
                self.status.files.append(f)

    def get_file_paths(self) -> list:
        """
        Get the paths of the files in the status.

        Returns
        -------
        list
            Paths of the files in the status.
        """
        return [f.get("path") for f in self.status.files]

    ##############################
    #  Private Helpers
    ##############################

    def _update_files_info(self, files_info: list[dict] | None = None) -> None:
        """
        Update files info.

        Parameters
        ----------
        files_info : list[dict] | None
            Files info.
        """
        if files_info is None:
            return
        if self.status.files:
            self.refresh()
        self.add_files_info(files_info)
        self.save(update=True)

    def _get_files_info(self) -> None:
        """
        Get files info from backend.
        """
        if not self._context().local and not self.status.files:
            files = context_processor.read_files_info(
                project=self.project,
                entity_type=self.ENTITY_TYPE,
                entity_id=self.id,
            )
            self.add_files_info(files)
