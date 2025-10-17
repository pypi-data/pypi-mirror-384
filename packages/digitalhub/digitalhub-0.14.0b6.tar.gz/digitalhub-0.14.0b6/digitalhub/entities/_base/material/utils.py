# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path

from digitalhub.stores.data.api import get_default_store
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.file_utils import eval_zip_type
from digitalhub.utils.uri_utils import has_local_scheme


def eval_local_source(source: str | list[str]) -> None:
    """
    Evaluate if source is local.

    Parameters
    ----------
    source : str | list[str]
        Source(s).
    """
    if isinstance(source, list):
        if not source:
            raise ValueError("Empty list of sources.")
        source_is_local = all(has_local_scheme(s) for s in source)
        for s in source:
            if Path(s).is_dir():
                raise ValueError(f"Invalid source path: {s}. List of paths must be list of files, not directories.")
    else:
        source_is_local = has_local_scheme(source)

    if not source_is_local:
        raise ValueError("Invalid source path. Source must be a local path.")


def eval_zip_sources(source: str | list[str]) -> bool:
    """
    Evaluate zip sources.

    Parameters
    ----------
    source : str | list[str]
        Source(s).

    Returns
    -------
    bool
        True if source is zip.
    """
    if isinstance(source, list):
        if len(source) > 1:
            return False
        path = source[0]
    else:
        if Path(source).is_dir():
            return False
        path = source

    if not eval_zip_type(path):
        return False
    return True


def build_log_path_from_source(
    project: str,
    entity_type: str,
    name: str,
    uuid: str,
    source: str | list[str],
) -> str:
    """
    Build log path.

    Parameters
    ----------
    project : str
        Project name.
    entity_type : str
        Entity type.
    name : str
        Object name.
    uuid : str
        Object UUID.
    source : str | list[str]
        Source(s).

    Returns
    -------
    str
        Log path.
    """
    prefix = "zip+" if eval_zip_sources(source) else ""
    path = f"{prefix}{get_default_store(project)}/{project}/{entity_type}/{name}/{uuid}"

    if isinstance(source, list) and len(source) >= 1:
        if len(source) > 1:
            path += "/"
        else:
            path += f"/{Path(source[0]).name}"
    elif Path(source).is_dir():
        path += "/"
    elif Path(source).is_file():
        path += f"/{Path(source).name}"

    return path


def refresh_decorator(fn: typing.Callable) -> typing.Callable:
    """
    Refresh decorator.

    Parameters
    ----------
    fn : Callable
        Function to decorate.

    Returns
    -------
    Callable
        Decorated function.
    """

    def wrapper(self, *args, **kwargs):
        # Prevent rising error if entity is not yet created in backend
        try:
            self.refresh()
        except BackendError:
            pass
        return fn(self, *args, **kwargs)

    return wrapper
