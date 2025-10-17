# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import importlib.util as imputil
import json
from datetime import date, datetime, time
from enum import Enum, EnumMeta
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable
from warnings import warn
from zipfile import ZipFile

import numpy as np
import requests
from slugify import slugify

from digitalhub.utils.io_utils import read_text


def get_timestamp() -> str:
    """
    Get the current timestamp in ISO format with timezone.

    Returns
    -------
    str
        The current timestamp in ISO format with timezone.
    """
    return datetime.now().astimezone().isoformat()


def decode_base64_string(string: str) -> str:
    """
    Decode a string from base64 encoding.

    Parameters
    ----------
    string : str
        The base64-encoded string to decode.

    Returns
    -------
    str
        The decoded string.
    """
    return base64.b64decode(string).decode()


def encode_string(string: str) -> str:
    """
    Encode a string in base64.

    Parameters
    ----------
    string : str
        The string to encode.

    Returns
    -------
    str
        The base64-encoded string.
    """
    return base64.b64encode(string.encode()).decode()


def encode_source(path: str) -> str:
    """
    Read a file and encode its content in base64.

    Parameters
    ----------
    path : str
        The file path to read.

    Returns
    -------
    str
        The file content encoded in base64.
    """
    return encode_string(read_text(path))


def requests_chunk_download(source: str, filename: Path) -> None:
    """
    Download a file from a URL in chunks and save to disk.

    Parameters
    ----------
    source : str
        URL to download the file from.
    filename : Path
        Path where to save the downloaded file.
    """
    with requests.get(source, stream=True) as r:
        r.raise_for_status()
        with filename.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def extract_archive(path: Path, filename: Path) -> None:
    """
    Extract a zip archive to a specified directory.

    Parameters
    ----------
    path : Path
        Directory where to extract the archive.
    filename : Path
        Path to the zip archive file.
    """
    with ZipFile(filename, "r") as zip_file:
        zip_file.extractall(path)


class CustomJsonEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle serialization of special types.
    """

    def default(self, obj: Any) -> Any:
        """
        Convert an object to a JSON-serializable format.

        Parameters
        ----------
        obj : Any
            The object to convert.

        Returns
        -------
        Any
            The object converted to a JSON-serializable format.
        """
        if isinstance(obj, (int, str, float, list, dict)):
            return obj
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return str(obj)


def dump_json(struct: Any) -> str:
    """
    Convert a Python object to a JSON string using CustomJsonEncoder.

    Parameters
    ----------
    struct : Any
        The object to convert to JSON.

    Returns
    -------
    str
        The JSON string representation of the object.
    """
    return json.dumps(struct, cls=CustomJsonEncoder)


def slugify_string(filename: str) -> str:
    """
    Sanitize a filename using slugify.

    Parameters
    ----------
    filename : str
        The filename to sanitize.

    Returns
    -------
    str
        The sanitized filename (max length 255).
    """
    return slugify(filename, max_length=255)


def import_function(path: Path, handler: str) -> Callable:
    """
    Import a function from a Python module file.

    Parameters
    ----------
    path : Path
        Path to the Python module file.
    handler : str
        Name of the function to import.

    Returns
    -------
    Callable
        The imported function.

    Raises
    ------
    RuntimeError
        If the module or function cannot be loaded or is not callable.
    """
    spec = imputil.spec_from_file_location(path.stem, path)
    if spec is None:
        raise RuntimeError(f"Error loading function source from {str(path)}.")

    mod = imputil.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Error getting module loader from {str(path)}.")

    spec.loader.exec_module(mod)
    func = getattr(mod, handler)
    if not callable(func):
        raise RuntimeError(f"Handler '{handler}' is not a callable.")

    return func


def list_enum(enum: EnumMeta) -> list[Any]:
    """
    Get all values of an enum class.

    Parameters
    ----------
    enum : EnumMeta
        Enum class to get values from.

    Returns
    -------
    list
        List of enum values.
    """
    vals: MappingProxyType[str, Enum] = enum.__members__
    return [member.value for member in vals.values()]


def carriage_return_warn(string: str) -> None:
    """
    Print a warning message if the string contains
    a carriage return (\r\n).

    Parameters
    ----------
    string : str
        The string to check.
    """
    if "\r\n" in string:
        warn("String contains a carriage return. It may not be parsed correctly from remote runtimes.")


def read_source(path: str) -> str:
    """
    Read a file and encode its content in base64,
    warning if carriage returns are present.

    Parameters
    ----------
    path : str
        Path to the file.

    Returns
    -------
    str
        Base64-encoded file content.
    """
    text = read_text(path)
    carriage_return_warn(text)
    return encode_string(text)
