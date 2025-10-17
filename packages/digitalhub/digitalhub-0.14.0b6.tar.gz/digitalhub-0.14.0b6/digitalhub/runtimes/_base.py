# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Callable

from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.logger import LOGGER


class Runtime:
    """
    Base Runtime class for executing tasks in the DigitalHub platform.

    Runtimes are the entities responsible for the actual execution
    of a given run. They are highly specialized components which
    can translate the representation of a given execution as expressed
    in the run into an actual execution operation performed via
    libraries, code, external tools etc.
    """

    def __init__(self, project: str) -> None:
        self.project = project

    @abstractmethod
    def build(self, executable: dict, task: dict, run: dict) -> dict:
        """
        Build run specification from executable, task and run configurations.
        """

    @abstractmethod
    def run(self, run: dict) -> dict:
        """
        Execute run task based on the run specification.
        """

    ##############################
    # Private methods
    ##############################

    def _validate_task(self, run: dict) -> str:
        """
        Check if task is allowed by validating against allowed actions.

        This method presumes that the runtime holds a list of allowed actions
        in the self.allowed_actions attribute.

        Parameters
        ----------
        run : dict
            Run object dictionary.

        Returns
        -------
        str
            The validated action name to execute.

        Raises
        ------
        RuntimeError
            If the run specification is malformed or task is not allowed.
        """
        try:
            task_kind = run["spec"]["task"].split(":")[0]
        except (KeyError, IndexError):
            msg = "Malformed run spec."
            LOGGER.exception(msg)
            raise RuntimeError(msg)

        try:
            return entity_factory.get_action_from_task_kind(task_kind, task_kind)
        except EntityError:
            msg = f"Task {task_kind} not allowed."
            LOGGER.exception(msg)
            raise RuntimeError(msg)

    @staticmethod
    def _execute(func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with provided arguments safely.

        Parameters
        ----------
        func : Callable
            Function to execute.
        *args
            Function arguments.
        **kwargs
            Function keyword arguments.

        Returns
        -------
        Any
            Function return value.

        Raises
        ------
        RuntimeError
            If any exception occurs during function execution.
        """
        try:
            return func(*args, **kwargs)
        except Exception:
            msg = "Something got wrong during function execution."
            LOGGER.exception(msg)
            raise RuntimeError(msg)
