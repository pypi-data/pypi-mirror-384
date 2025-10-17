# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.builder import context_builder

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities.project._base.entity import Project


def build_context(project: Project, overwrite: bool = False) -> Context:
    """
    Build a new context for a project.

    Creates or updates a context instance for the given project
    in the global context registry.

    Parameters
    ----------
    project : Project
        The project object used to build the context.
    overwrite : bool
        If True, overwrites existing context if it exists. Default is False.

    Returns
    -------
    Context
        The newly created or existing context instance.
    """
    return context_builder.build(project, overwrite)


def get_context(project: str) -> Context:
    """
    Get the context for a given project name.

    Parameters
    ----------
    project : str
        Project name.

    Returns
    -------
    Context
        The context for the given project name.
    """
    return context_builder.get(project)


def delete_context(project: str) -> None:
    """
    Delete the context for a given project name.

    Parameters
    ----------
    project : str
        Project name.
    """
    context_builder.remove(project)
