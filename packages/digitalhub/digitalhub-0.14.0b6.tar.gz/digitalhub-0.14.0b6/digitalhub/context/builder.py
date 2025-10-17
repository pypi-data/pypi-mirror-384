# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.context import Context
from digitalhub.utils.exceptions import ContextError

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project


class ContextBuilder:
    """
    A builder class for managing project contexts.

    This class implements the builder pattern to create and manage Context instances.
    It maintains a registry of project contexts, allowing multiple projects to be
    used simultaneously by storing them with their respective names.

    Attributes
    ----------
    _instances : dict[str, Context]
        Internal registry mapping project names to their Context instances.
    """

    def __init__(self) -> None:
        self._instances: dict[str, Context] = {}

    def build(self, project: Project, overwrite: bool = False) -> Context:
        """
        Add a project as context and return the created Context instance.

        Parameters
        ----------
        project : Project
            The project instance to create a context for.
        overwrite : bool
            If True, overwrites existing context if project name already exists. Default is False.

        Returns
        -------
        Context
            The newly created or existing Context instance.
        """
        if (project.name not in self._instances) or overwrite:
            self._instances[project.name] = Context(project)
        return self._instances[project.name]

    def get(self, project: str) -> Context:
        """
        Retrieve a context instance by project name.

        Parameters
        ----------
        project : str
            The name of the project whose context to retrieve.

        Returns
        -------
        Context
            The context instance associated with the project.

        Raises
        ------
        ContextError
            If no context exists for the specified project name.
        """
        try:
            return self._instances[project]
        except KeyError:
            raise ContextError(f"Context '{project}' not found. Get or create a project named '{project}'.")

    def remove(self, project: str) -> None:
        """
        Remove a project's context from the registry.

        Parameters
        ----------
        project : str
            The name of the project whose context should be removed.
            This method does not return anything.

        Notes
        -----
        If the project does not exist in the registry, this method silently does nothing.
        """
        self._instances.pop(project, None)


context_builder = ContextBuilder()
