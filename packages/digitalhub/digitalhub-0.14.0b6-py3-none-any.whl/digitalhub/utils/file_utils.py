# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from mimetypes import guess_type
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class FileInfo(BaseModel):
    """
    File info class.

    Attributes
    ----------
    path : str or None
        Path to the file.
    name : str or None
        Name of the file.
    content_type : str or None
        MIME type of the file.
    size : int or None
        Size of the file in bytes.
    hash : str or None
        Hash of the file contents.
    last_modified : str or None
        Last modified date/time in ISO format.
    """

    path: Optional[str] = None
    name: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    hash: Optional[str] = None
    last_modified: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert FileInfo to dictionary.

        Returns
        -------
        dict
            Dictionary representation of the FileInfo object.
        """
        return self.model_dump()


def calculate_blob_hash(data_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Parameters
    ----------
    data_path : str
        Path to the file.

    Returns
    -------
    str
        The SHA-256 hash of the file, prefixed with 'sha256:'.
    """
    with open(data_path, "rb") as f:
        data = f.read()
        return f"sha256:{sha256(data).hexdigest()}"


def get_file_size(data_path: str) -> int:
    """
    Get the size of a file in bytes.

    Parameters
    ----------
    data_path : str
        Path to the file.

    Returns
    -------
    int
        Size of the file in bytes.
    """
    return Path(data_path).stat().st_size


def get_file_mime_type(data_path: str) -> str | None:
    """
    Get the MIME type of a file.

    Parameters
    ----------
    data_path : str
        Path to the file.

    Returns
    -------
    str or None
        The MIME type of the file, or None if unknown.
    """
    return guess_type(data_path)[0]


def get_path_name(data_path: str) -> str:
    """
    Get the name of a file from its path.

    Parameters
    ----------
    data_path : str
        Path to the file.

    Returns
    -------
    str
        The name of the file.
    """
    return Path(data_path).name


def get_last_modified(data_path: str) -> str:
    """
    Get the last modified date/time of a file in ISO format.

    Parameters
    ----------
    data_path : str
        Path to the file.

    Returns
    -------
    str
        The last modified date/time in ISO format.
    """
    path = Path(data_path)
    timestamp = path.stat().st_mtime
    return datetime.fromtimestamp(timestamp).astimezone().isoformat()


def get_file_info_from_local(path: str, src_path: str) -> None | dict:
    """
    Get file info from a local path.

    Parameters
    ----------
    path : str
        Target path of the object.
    src_path : str
        Local path of the source file.

    Returns
    -------
    dict or None
        File info dictionary, or None if an error occurs.
    """
    try:
        name = get_path_name(path)
        content_type = get_file_mime_type(path)
        size = get_file_size(path)
        hash = calculate_blob_hash(path)
        last_modified = get_last_modified(path)

        return FileInfo(
            path=src_path,
            name=name,
            content_type=content_type,
            size=size,
            hash=hash,
            last_modified=last_modified,
        ).to_dict()
    except Exception:
        return None


def get_file_info_from_s3(path: str, metadata: dict) -> None | dict:
    """
    Get file info from S3 metadata.

    Parameters
    ----------
    path : str
        Object source path.
    metadata : dict
        Metadata dictionary of the object from S3.

    Returns
    -------
    dict or None
        File info dictionary, or None if an error occurs.
    """
    try:
        size = metadata["ContentLength"]
        file_hash = metadata["ETag"][1:-1]

        file_size_limit_multipart = 20 * 1024 * 1024
        if size < file_size_limit_multipart:
            file_hash = "md5:" + file_hash
        else:
            file_hash = "ETag:" + file_hash

        name = get_path_name(path)
        content_type = metadata["ContentType"]
        last_modified = metadata["LastModified"].isoformat()

        return FileInfo(
            path=path,
            name=name,
            content_type=content_type,
            size=size,
            hash=file_hash,
            last_modified=last_modified,
        ).to_dict()
    except Exception:
        return None


def eval_zip_type(source: str) -> bool:
    """
    Evaluate whether the source is a zip file.

    Parameters
    ----------
    source : str
        Source file path.

    Returns
    -------
    bool
        True if the path is a zip file, False otherwise.
    """
    extension = source.endswith(".zip")
    mime_zip = get_file_mime_type(source) == "application/zip"
    return extension or mime_zip


def eval_text_type(source: str) -> bool:
    """
    Evaluate whether the source is a plain text file.

    Parameters
    ----------
    source : str
        Source file path.

    Returns
    -------
    bool
        True if the path is a plain text file, False otherwise.
    """
    return get_file_mime_type(source) == "text/plain"


def eval_py_type(source: str) -> bool:
    """
    Evaluate whether the source is a Python file.

    Parameters
    ----------
    source : str
        Source file path.

    Returns
    -------
    bool
        True if the path is a Python file, False otherwise.
    """
    extension = source.endswith(".py")
    mime_py = get_file_mime_type(source) == "text/x-python"
    return extension or mime_py
