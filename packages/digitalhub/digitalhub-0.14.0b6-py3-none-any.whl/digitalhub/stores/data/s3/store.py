# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from io import BytesIO
from pathlib import Path
from typing import Any, Type
from urllib.parse import urlparse

import boto3
import botocore.client  # pylint: disable=unused-import
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError, NoCredentialsError

from digitalhub.stores.data._base.store import Store
from digitalhub.stores.readers.data.api import get_reader_by_object
from digitalhub.utils.exceptions import ConfigError, StoreError
from digitalhub.utils.file_utils import get_file_info_from_s3, get_file_mime_type
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.stores.credentials.configurator import Configurator
    from digitalhub.stores.data.s3.configurator import S3StoreConfigurator


# Type aliases
S3Client = Type["botocore.client.S3"]

MULTIPART_THRESHOLD = 100 * 1024 * 1024


class S3Store(Store):
    """
    S3 store class. It implements the Store interface and provides methods to fetch and persist
    artifacts on S3 based storage.
    """

    def __init__(self, configurator: Configurator | None = None) -> None:
        super().__init__(configurator)
        self._configurator: S3StoreConfigurator

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
        client, bucket = self._check_factory(src)

        # Build destination directory
        if dst.suffix == "":
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)

        # Handle src and tree destination
        if self.is_partition(src):
            keys = self._list_objects(client, bucket, src)
            strip_root = self._get_key(src)
            trees = [k.removeprefix(strip_root) for k in keys]
        else:
            keys = [self._get_key(src)]
            trees = [Path(self._get_key(src)).name]

        if len(keys) != len(trees):
            raise StoreError("Keys and trees must have the same length.")

        # Download files
        for elements in zip(keys, trees):
            key = elements[0]
            tree = elements[1]

            # Build destination path
            if dst.suffix == "":
                dst_pth = Path(dst, tree)
            else:
                dst_pth = dst

            # Check if destination path already exists
            self._check_overwrite(dst_pth, overwrite)

            self._build_path(dst_pth.parent)

            self._download_file(key, dst_pth, client, bucket)

        if len(trees) == 1:
            if dst.suffix == "":
                return str(Path(dst, trees[0]))
        return str(dst)

    def upload(
        self,
        src: SourcesOrListOfSources,
        dst: str,
    ) -> list[tuple[str, str]]:
        """
        Upload an artifact to storage.

        Parameters
        ----------
        src : SourcesOrListOfSources
            Source(s).
        dst : str
            The destination of the material entity on storage.

        Returns
        -------
        list[tuple[str, str]]
            Returns the list of destination and source paths of the uploaded artifacts.
        """
        # Destination handling
        key = self._get_key(dst)

        # Source handling (files list, dir or single file)
        src_is_list = isinstance(src, list)
        if not src_is_list:
            self._check_local_src(src)
            src_is_dir = Path(src).is_dir()
        else:
            for s in src:
                self._check_local_src(s)
            src_is_dir = False
            if len(src) == 1:
                src = src[0]

        # If source is a directory, destination must be a partition
        if (src_is_dir or src_is_list) and not dst.endswith("/"):
            raise StoreError(
                "If source is a list of files or a directory, "
                "destination must be a partition, e.g. 's3://bucket/partition/'"
            )

        # S3 client
        client, bucket = self._check_factory(dst)

        # Directory
        if src_is_dir:
            return self._upload_dir(src, key, client, bucket)

        # List of files
        elif src_is_list:
            return self._upload_file_list(src, key, client, bucket)

        # Single file
        return self._upload_single_file(src, key, client, bucket)

    def upload_fileobject(
        self,
        src: BytesIO,
        dst: str,
    ) -> str:
        """
        Upload an BytesIO to S3 based storage.

        Parameters
        ----------
        src : BytesIO
            The source object to be persisted.
        dst : str
            The destination path of the artifact.

        Returns
        -------
        str
            S3 key of the uploaded artifact.
        """
        client, bucket = self._check_factory(dst)
        key = self._get_key(dst)
        self._upload_fileobject(src, key, client, bucket)
        return f"s3://{bucket}/{key}"

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
        client, bucket = self._check_factory(root)

        infos = []
        for i in paths:
            key, src_path = i

            # Rebuild key in case here arrive an s3://bucket prefix
            key = self._get_key(key)

            # Get metadata
            metadata = client.head_object(Bucket=bucket, Key=key)

            # Get file info
            info = get_file_info_from_s3(src_path, metadata)
            infos.append(info)

        return infos

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

        # Verify if partition or single file
        if self.is_partition(path):
            client, bucket = self._check_factory(path)
            objects = self._list_objects(client, bucket, path)
            keys = [self._get_key(o) for o in objects]

        else:
            if isinstance(path, list):
                client, bucket = self._check_factory(path[0])
                keys = [self._get_key(p) for p in path]
            else:
                client, bucket = self._check_factory(path)
                keys = [self._get_key(path)]

        dfs = []
        for key in keys:
            file_format = self._get_extension(file_format, key)
            obj = self._download_fileobject(key, client, bucket)
            dfs.append(reader.read_df(obj, extension=file_format, **kwargs))

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
        raise StoreError("S3 store does not support query.")

    def write_df(
        self,
        df: Any,
        dst: str,
        extension: str | None = None,
        **kwargs,
    ) -> str:
        """
        Write a dataframe to S3 based storage. Kwargs are passed to df.to_parquet().

        Parameters
        ----------
        df : Any
            The dataframe.
        dst : str
            The destination path on S3 based storage.
        extension : str
            The extension of the file.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        str
            The S3 path where the dataframe was saved.
        """
        reader = get_reader_by_object(df)
        with BytesIO() as fileobj:
            reader.write_df(df, fileobj, extension=extension, **kwargs)
            fileobj.seek(0)
            return self.upload_fileobject(fileobj, dst)

    ##############################
    # Wrapper methods
    ##############################

    def get_s3_source(self, src: str, filename: Path) -> None:
        """
        Download a file from S3 and save it to a local file.

        Parameters
        ----------
        src : str
            S3 path of the object to be downloaded (e.g., 's3://bucket
        filename : Path
            Local path where the downloaded object will be saved.
        """
        client, bucket = self._check_factory(src)
        key = self._get_key(src)
        self._download_file(key, filename, client, bucket)

    def get_s3_client(self, file: bool = True) -> S3Client:
        """
        Get an S3 client object.

        Parameters
        ----------
        file : bool
            Whether to use file-based credentials. Default is True.

        Returns
        -------
        S3Client
            Returns a client object that interacts with the S3 storage service.
        """
        if file:
            cfg = self._configurator.get_file_config()
        else:
            cfg = self._configurator.get_env_config()
        return self._get_client(cfg)

    ##############################
    # Private I/O methods
    ##############################

    @staticmethod
    def _download_file(
        key: str,
        dst_pth: Path,
        client: S3Client,
        bucket: str,
    ) -> list[str]:
        """
        Download files from S3 partition.

        Parameters
        ----------
        key : str
            The key to be downloaded.
        dst_pth : str
            The destination of the files on local filesystem.
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.

        Returns
        -------
        list[str]
            The list of paths of the downloaded files.
        """
        client.download_file(bucket, key, dst_pth)

    @staticmethod
    def _download_fileobject(
        key: str,
        client: S3Client,
        bucket: str,
    ) -> BytesIO:
        """
        Download fileobject from S3 partition.

        Parameters
        ----------
        key : str
            The key of the file.
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.

        Returns
        -------
        BytesIO
            The fileobject of the downloaded file.
        """
        obj = client.get_object(Bucket=bucket, Key=key)
        return BytesIO(obj["Body"].read())

    def _upload_dir(
        self,
        src: str,
        dst: str,
        client: S3Client,
        bucket: str,
    ) -> list[tuple[str, str]]:
        """
        Upload directory to storage.

        Parameters
        ----------
        src : str
            List of sources.
        dst : str
            The destination of the material entity on storage.
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.

        Returns
        -------
        list[tuple[str, str]]
            Returns the list of destination and source paths of the uploaded artifacts.
        """
        # Get list of files
        src_pth = Path(src)
        files = [i for i in src_pth.rglob("*") if i.is_file()]

        # Build keys
        keys = []
        for i in files:
            i = i.relative_to(src_pth)
            keys.append(f"{dst}{i}")

        # Upload files
        paths = []
        for f, k in zip(files, keys):
            self._upload_file(f, k, client, bucket)
            paths.append((k, str(f.relative_to(src_pth))))
        return paths

    def _upload_file_list(
        self,
        src: list[str],
        dst: str,
        client: S3Client,
        bucket: str,
    ) -> list[tuple[str, str]]:
        """
        Upload list of files to storage.

        Parameters
        ----------
        src : list
            List of sources.
        dst : str
            The destination of the material entity on storage.
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.

        Returns
        -------
        list[tuple[str, str]]
            Returns the list of destination and source paths of the uploaded artifacts.
        """
        files = src
        keys = []
        for i in files:
            keys.append(f"{dst}{Path(i).name}")
        if len(set(keys)) != len(keys):
            raise StoreError("Keys must be unique (Select files with different names, otherwise upload a directory).")

        # Upload files
        paths = []
        for f, k in zip(files, keys):
            self._upload_file(f, k, client, bucket)
            paths.append((k, Path(f).name))
        return paths

    def _upload_single_file(
        self,
        src: str,
        dst: str,
        client: S3Client,
        bucket: str,
    ) -> str:
        """
        Upload a single file to storage.

        Parameters
        ----------
        src : str
            List of sources.
        dst : str
            The destination of the material entity on storage.
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.

        Returns
        -------
        str
            Returns the list of destination and source paths of the uploaded artifacts.
        """
        if dst.endswith("/"):
            dst = f"{dst.removeprefix('/')}{Path(src).name}"

        # Upload file
        self._upload_file(src, dst, client, bucket)
        name = Path(self._get_key(dst)).name
        return [(dst, name)]

    @staticmethod
    def _upload_file(
        src: str,
        key: str,
        client: S3Client,
        bucket: str,
    ) -> None:
        """
        Upload a file to S3 based storage. The function checks if the
        bucket is accessible.

        Parameters
        ----------
        src : str
            The source path of the file on local filesystem.
        key : str
            The key of the file on S3 based storage.
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.
        """
        extra_args = {}
        mime_type = get_file_mime_type(src)
        if mime_type is not None:
            extra_args["ContentType"] = mime_type
        client.upload_file(
            Filename=src,
            Bucket=bucket,
            Key=key,
            ExtraArgs=extra_args,
            Config=TransferConfig(multipart_threshold=MULTIPART_THRESHOLD),
        )

    @staticmethod
    def _upload_fileobject(
        fileobj: BytesIO,
        key: str,
        client: S3Client,
        bucket: str,
    ) -> None:
        """
        Upload a fileobject to S3 based storage. The function checks if the bucket is accessible.

        Parameters
        ----------
        fileobj : BytesIO
            The fileobject to be uploaded.
        key : str
            The key of the file on S3 based storage.
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.
        """
        client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=bucket,
            Key=key,
            Config=TransferConfig(multipart_threshold=MULTIPART_THRESHOLD),
        )

    ##############################
    # Helper methods
    ##############################

    def _get_bucket(self, root: str) -> str:
        """
        Get the name of the S3 bucket from the URI.

        Returns
        -------
        str
            The name of the S3 bucket.
        """
        return urlparse(root).netloc

    def _get_client(self, cfg: dict) -> S3Client:
        """
        Get an S3 client object.

        Parameters
        ----------
        cfg : dict
            The configuration of the S3 client.

        Returns
        -------
        S3Client
            Returns a client object that interacts with the S3 storage service.
        """
        return boto3.client("s3", **cfg)

    def _check_factory(self, s3_path: str, retry: bool = True) -> tuple[S3Client, str]:
        """
        Checks if the S3 bucket collected from the URI is accessible.

        Parameters
        ----------
        s3_path : str
            Path to the S3 bucket (e.g., 's3://bucket/path').
        retry : bool
            Whether to retry the operation if a ConfigError is raised. Default is True.

        Returns
        -------
        tuple of S3Client and str
            Tuple containing the S3 client object and the name of the S3 bucket.

        Raises
        ------
        ConfigError
            If access to the specified bucket is not available and retry is False.
        """
        bucket = self._get_bucket(s3_path)
        try:
            cfg = self._configurator.get_client_config()
            client = self._get_client(cfg)
            self._check_access_to_storage(client, bucket)
            return client, bucket
        except ConfigError as e:
            if retry:
                self._configurator.eval_change_origin()
                return self._check_factory(s3_path, False)
            raise e

    def _check_access_to_storage(self, client: S3Client, bucket: str) -> None:
        """
        Checks if the S3 bucket is accessible by sending a head_bucket request.

        Parameters
        ----------
        client : S3Client
            S3 client object.
        bucket : str
            Name of the S3 bucket.

        Raises
        ------
        ConfigError
            If access to the specified bucket is not available.
        """
        try:
            client.head_bucket(Bucket=bucket)
        except (ClientError, NoCredentialsError) as err:
            raise ConfigError(f"No access to s3 bucket! Error: {err}")

    @staticmethod
    def _get_key(path: str) -> str:
        """
        Build key.

        Parameters
        ----------
        path : str
            The source path to get the key from.

        Returns
        -------
        str
            The key.
        """
        key = urlparse(path).path.replace("\\", "/")
        if key.startswith("/"):
            key = key[1:]
        return key

    def _list_objects(self, client: S3Client, bucket: str, partition: str) -> list[str]:
        """
        List objects in a S3 partition.

        Parameters
        ----------
        client : S3Client
            The S3 client object.
        bucket : str
            The name of the S3 bucket.
        partition : str
            The partition.

        Returns
        -------
        list[str]
            The list of keys under the partition.
        """
        key = self._get_key(partition)
        file_list = client.list_objects_v2(Bucket=bucket, Prefix=key).get("Contents", [])
        return [f["Key"] for f in file_list]

    @staticmethod
    def is_partition(path: str) -> bool:
        """
        Check if path is a directory or a partition.

        Parameters
        ----------
        path : str
            The path to check.

        Returns
        -------
        bool
        """
        if path.endswith("/"):
            return True
        return False
