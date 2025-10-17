# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.entities._base.material.utils import build_log_path_from_source, eval_local_source
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._constructors.uuid import build_uuid


def eval_source(
    source: str | list[str] | None = None,
) -> Any:
    """
    Evaluate whether the source is local or remote.

    Determines if the provided source(s) reference local files or
    remote resources. This evaluation affects how the artifact
    will be processed and stored.

    Parameters
    ----------
    source : str, list[str], or None
        The source specification(s) to evaluate. Can be a single
        source string, a list of source strings, or None.

    Returns
    -------
    Any
        The result of the local source evaluation, indicating
        whether the source is local or remote.
    """
    return eval_local_source(source)


def process_kwargs(
    project: str,
    name: str,
    source: str | list[str],
    path: str | None = None,
    **kwargs,
) -> dict:
    """
    Process and enhance specification parameters for artifact creation.

    Processes the keyword arguments for artifact specification, handling
    path generation and UUID assignment. If no path is provided, generates
    a unique path based on project, entity type, name, and source.

    Parameters
    ----------
    project : str
        The name of the project.
    name : str
        The name of the artifact entity.
    source : str or list[str]
        The source specification(s) for the artifact content.
        Can be a single source or multiple sources.
    path : str
        The destination path for the artifact entity.
        If None, a path will be automatically generated.
    **kwargs : dict
        Additional specification parameters to be processed
        and passed to the artifact creation.

    Returns
    -------
    dict
        The updated kwargs dictionary with processed path
        and UUID information included.
    """
    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        kwargs["path"] = build_log_path_from_source(project, EntityTypes.ARTIFACT.value, name, uuid, source)
    else:
        kwargs["path"] = path
    return kwargs
