# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.trigger._base.spec import TriggerSpec, TriggerValidator


class TriggerSpecScheduler(TriggerSpec):
    """
    TriggerSpecScheduler specifications.
    """

    def __init__(
        self,
        task: str,
        template: dict,
        function: str | None = None,
        workflow: str | None = None,
        schedule: str | None = None,
    ) -> None:
        super().__init__(task, template, function, workflow)
        self.schedule = schedule


class TriggerValidatorScheduler(TriggerValidator):
    """
    TriggerValidatorScheduler validator.
    """

    schedule: str
    """Quartz cron expression."""
