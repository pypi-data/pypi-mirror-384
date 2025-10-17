# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.utils import KindAction
from digitalhub.utils.exceptions import EntityError


class RuntimeEntityBuilder:
    """
    RuntimeEntity builder.
    """

    EXECUTABLE_KIND: str = None
    TASKS_KINDS: list[KindAction] = None
    RUN_KINDS: list[KindAction] = None

    def __init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """
        Validate the entity.
        """
        for attr_name in ["EXECUTABLE_KIND", "TASKS_KINDS", "RUN_KINDS"]:
            value = getattr(self, attr_name)
            if value is None:
                raise EntityError(f"{attr_name} must be set")

        for attr_name in ["TASKS_KINDS", "RUN_KINDS"]:
            self._instance_validation(getattr(self, attr_name))

    def _instance_validation(self, attribute: list[KindAction]) -> None:
        """
        Validate if the attribute is a list of KindAction.

        Parameters
        ----------
        attribute : list[KindAction]
            Attribute to validate.
        """
        if not isinstance(attribute, list):
            raise EntityError(f"{attribute} must be a list")
        for i in attribute:
            if not isinstance(i, KindAction):
                raise EntityError(f"{attribute} must be a list of KindAction")
            if i.kind is None:
                raise EntityError(f"{attribute} must be a list of KindAction with kind set")

    def get_action_from_task_kind(self, task_kind: str) -> str:
        """
        Get action from task kind.

        Parameters
        ----------
        task_kind : str
            Task kind.

        Returns
        -------
        str
            Action.
        """
        for task in self.TASKS_KINDS:
            if task.kind == task_kind:
                return task.action
        msg = f"Task kind {task_kind} not allowed."
        raise EntityError(msg)

    def get_task_kind_from_action(self, action: str) -> list[str]:
        """
        Get task kinds from action.

        Parameters
        ----------
        action : str
            Action.

        Returns
        -------
        list[str]
            Task kinds.
        """
        for task in self.TASKS_KINDS:
            if task.action == action:
                return task.kind
        msg = f"Action {action} not allowed."
        raise EntityError(msg)

    def get_run_kind_from_action(self, action: str) -> str:
        """
        Get run kind from action.

        Parameters
        ----------
        action : str
            Action.

        Returns
        -------
        str
            Run kind.
        """
        for run in self.RUN_KINDS:
            if run.action == action:
                return run.kind
        msg = f"Action {action} not allowed."
        raise EntityError(msg)

    def get_executable_kind(self) -> str:
        """
        Get executable kind.

        Returns
        -------
        str
            Executable kind.
        """
        return self.EXECUTABLE_KIND

    def get_all_kinds(self) -> list[str]:
        """
        Get all kinds.

        Returns
        -------
        list[str]
            All kinds.
        """
        task_kinds = [i.kind for i in self.TASKS_KINDS]
        run_kinds = [i.kind for i in self.RUN_KINDS]
        return [self.EXECUTABLE_KIND, *run_kinds, *task_kinds]

    def get_all_actions(self) -> list[str]:
        """
        Get all actions.

        Returns
        -------
        list[str]
            All actions.
        """
        return [i.action for i in self.TASKS_KINDS]
