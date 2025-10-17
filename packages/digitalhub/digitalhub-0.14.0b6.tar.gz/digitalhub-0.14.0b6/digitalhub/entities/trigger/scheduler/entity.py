# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.trigger._base.entity import Trigger

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.trigger.scheduler.spec import TriggerSpecScheduler
    from digitalhub.entities.trigger.scheduler.status import TriggerStatusScheduler


class TriggerScheduler(Trigger):
    """
    TriggerScheduler class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: TriggerSpecScheduler,
        status: TriggerStatusScheduler,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: TriggerSpecScheduler
        self.status: TriggerStatusScheduler
