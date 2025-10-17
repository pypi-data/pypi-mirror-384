# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model.mlflow.entity import ModelMlflow
from digitalhub.entities.model.mlflow.spec import ModelSpecMlflow, ModelValidatorMlflow
from digitalhub.entities.model.mlflow.status import ModelStatusMlflow


class ModelModelBuilder(ModelBuilder):
    """
    ModelMlflow builder.
    """

    ENTITY_CLASS = ModelMlflow
    ENTITY_SPEC_CLASS = ModelSpecMlflow
    ENTITY_SPEC_VALIDATOR = ModelValidatorMlflow
    ENTITY_STATUS_CLASS = ModelStatusMlflow
    ENTITY_KIND = EntityKinds.MODEL_MLFLOW.value
