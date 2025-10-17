# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator


class TriggerSpec(Spec):
    """
    TriggerSpec specifications.
    """

    def __init__(
        self,
        task: str,
        template: dict,
        function: str | None = None,
        workflow: str | None = None,
    ) -> None:
        super().__init__()
        self.task = task
        self.template = template
        self.function = function
        self.workflow = workflow


class TriggerValidator(SpecValidator):
    """
    TriggerValidator validator.
    """

    task: str
    """Task string."""

    template: dict
    """Template map."""

    function: str = None
    """Function string."""

    workflow: str = None
    """Workflow string."""
