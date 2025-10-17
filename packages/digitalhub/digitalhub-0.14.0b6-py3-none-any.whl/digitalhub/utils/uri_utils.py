# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from enum import Enum
from urllib.parse import unquote, urlparse

from digitalhub.utils.generic_utils import list_enum


class S3Schemes(Enum):
    """
    S3 URI schemes.
    """

    S3 = "s3"
    S3A = "s3a"
    S3N = "s3n"
    ZIP_S3 = "zip+s3"


class LocalSchemes(Enum):
    """
    Local URI schemes.
    """

    LOCAL = ""


class InvalidLocalSchemes(Enum):
    """
    Invalid local URI schemes.
    """

    FILE = "file"
    LOCAL = "local"


class RemoteSchemes(Enum):
    """
    Remote URI schemes.
    """

    HTTP = "http"
    HTTPS = "https"
    ZIP_HTTP = "zip+http"
    ZIP_HTTPS = "zip+https"


class SqlSchemes(Enum):
    """
    SQL URI schemes.
    """

    SQL = "sql"
    POSTGRESQL = "postgresql"


class GitSchemes(Enum):
    """
    Git URI schemes.
    """

    GIT = "git"
    GIT_HTTP = "git+http"
    GIT_HTTPS = "git+https"


class SchemeCategory(Enum):
    """
    URI scheme categories.
    """

    S3 = "s3"
    LOCAL = "local"
    REMOTE = "remote"
    SQL = "sql"
    GIT = "git"


def map_uri_scheme(uri: str) -> str:
    """
    Map a URI scheme to a common scheme category.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    str
        Mapped scheme category (e.g., 'local', 'remote', 's3', 'sql', 'git').

    Raises
    ------
    ValueError
        If the scheme is unknown or invalid.
    """
    # Check for Windows paths (e.g. C:\path\to\file or \\network\share)
    if re.match(r"^[a-zA-Z]:\\", uri) or uri.startswith(r"\\"):
        return SchemeCategory.LOCAL.value

    scheme = urlparse(uri).scheme
    if scheme in list_enum(LocalSchemes):
        return SchemeCategory.LOCAL.value
    if scheme in list_enum(InvalidLocalSchemes):
        raise ValueError("For local URI, do not use any scheme.")
    if scheme in list_enum(RemoteSchemes):
        return SchemeCategory.REMOTE.value
    if scheme in list_enum(S3Schemes):
        return SchemeCategory.S3.value
    if scheme in list_enum(SqlSchemes):
        return SchemeCategory.SQL.value
    if scheme in list_enum(GitSchemes):
        return SchemeCategory.GIT.value
    raise ValueError(f"Unknown scheme '{scheme}'!")


def has_local_scheme(uri: str) -> bool:
    """
    Check if a URI has a local scheme.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    bool
        True if the URI is local, False otherwise.
    """
    return map_uri_scheme(uri) == SchemeCategory.LOCAL.value


def has_remote_scheme(uri: str) -> bool:
    """
    Check if a URI has a remote scheme.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    bool
        True if the URI is remote, False otherwise.
    """
    return map_uri_scheme(uri) == SchemeCategory.REMOTE.value


def has_s3_scheme(uri: str) -> bool:
    """
    Check if a URI has an S3 scheme.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    bool
        True if the URI is S3, False otherwise.
    """
    return map_uri_scheme(uri) == SchemeCategory.S3.value


def has_sql_scheme(uri: str) -> bool:
    """
    Check if a URI has an SQL scheme.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    bool
        True if the URI is SQL, False otherwise.
    """
    return map_uri_scheme(uri) == SchemeCategory.SQL.value


def has_git_scheme(uri: str) -> bool:
    """
    Check if a URI has a git scheme.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    bool
        True if the URI is git, False otherwise.
    """
    return map_uri_scheme(uri) == SchemeCategory.GIT.value


def has_zip_scheme(uri: str) -> bool:
    """
    Check if a URI has a zip scheme.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    bool
        True if the URI is zip, False otherwise.
    """
    return uri.startswith("zip+")


def get_filename_from_uri(uri: str) -> str:
    """
    Get the filename from a URI.

    Parameters
    ----------
    uri : str
        URI string.

    Returns
    -------
    str
        Filename extracted from the URI.
    """
    return unquote(urlparse(uri).path).split("/")[-1]
