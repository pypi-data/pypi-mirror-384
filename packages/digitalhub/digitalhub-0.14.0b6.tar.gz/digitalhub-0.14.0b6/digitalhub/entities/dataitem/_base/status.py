# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.material.status import MaterialStatus


class DataitemStatus(MaterialStatus):
    """
    DataitemStatus status.
    """

    def __init__(
        self,
        state: str,
        message: str | None = None,
        files: list[dict] | None = None,
        preview: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(state, message, files)
        self.preview = preview
