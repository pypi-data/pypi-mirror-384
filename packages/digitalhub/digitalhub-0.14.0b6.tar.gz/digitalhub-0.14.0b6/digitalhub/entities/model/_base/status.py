# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.material.status import MaterialStatus


class ModelStatus(MaterialStatus):
    """
    ModelStatus status.
    """

    def __init__(
        self,
        state: str,
        message: str | None = None,
        files: list[dict] | None = None,
        metrics: dict | None = None,
    ):
        super().__init__(state, message, files)
        self.metrics = metrics if metrics is not None else {}
