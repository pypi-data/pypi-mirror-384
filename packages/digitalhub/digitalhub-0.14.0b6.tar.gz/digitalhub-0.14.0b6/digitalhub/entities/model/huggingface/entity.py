# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.model._base.entity import Model

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.model.huggingface.spec import ModelSpecHuggingface
    from digitalhub.entities.model.huggingface.status import ModelStatusHuggingface


class ModelHuggingface(Model):
    """
    ModelHuggingface class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: ModelSpecHuggingface,
        status: ModelStatusHuggingface,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: ModelSpecHuggingface
        self.status: ModelStatusHuggingface
