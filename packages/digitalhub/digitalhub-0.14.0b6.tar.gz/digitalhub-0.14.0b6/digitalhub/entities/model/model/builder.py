# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model.model.entity import ModelModel
from digitalhub.entities.model.model.spec import ModelSpecModel, ModelValidatorModel
from digitalhub.entities.model.model.status import ModelStatusModel


class ModelMlflowBuilder(ModelBuilder):
    """
    ModelModel builder.
    """

    ENTITY_CLASS = ModelModel
    ENTITY_SPEC_CLASS = ModelSpecModel
    ENTITY_SPEC_VALIDATOR = ModelValidatorModel
    ENTITY_STATUS_CLASS = ModelStatusModel
    ENTITY_KIND = EntityKinds.MODEL_MODEL.value
