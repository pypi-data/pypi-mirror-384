# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.model._base.entity import Model

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.model.mlflow.spec import ModelSpecMlflow
    from digitalhub.entities.model.mlflow.status import ModelStatusMlflow


class ModelMlflow(Model):
    """
    ModelMlflow class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: ModelSpecMlflow,
        status: ModelStatusMlflow,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: ModelSpecMlflow
        self.status: ModelStatusMlflow
