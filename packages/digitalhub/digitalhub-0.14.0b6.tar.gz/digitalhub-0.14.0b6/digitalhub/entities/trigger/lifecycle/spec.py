# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities.trigger._base.spec import TriggerSpec, TriggerValidator

regexp = r"store://([^/]+)/(.+)"


class TriggerSpecLifecycle(TriggerSpec):
    """
    TriggerSpecLifecycle specifications.
    """

    def __init__(
        self,
        task: str,
        template: dict,
        function: str | None = None,
        workflow: str | None = None,
        key: str | None = None,
        states: list[str] | None = None,
    ) -> None:
        super().__init__(task, template, function, workflow)
        self.key = key
        self.states = states


class TriggerValidatorLifecycle(TriggerValidator):
    """
    TriggerValidatorLifecycle validator.
    """

    key: str = Field(pattern=regexp)
    """Entity key."""

    states: list[str] = None
    """List of entity states."""
