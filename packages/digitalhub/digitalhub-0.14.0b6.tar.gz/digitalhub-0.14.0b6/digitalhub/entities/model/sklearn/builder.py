# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model.sklearn.entity import ModelSklearn
from digitalhub.entities.model.sklearn.spec import ModelSpecSklearn, ModelValidatorSklearn
from digitalhub.entities.model.sklearn.status import ModelStatusSklearn


class ModelSklearnBuilder(ModelBuilder):
    """
    ModelSklearn builder.
    """

    ENTITY_CLASS = ModelSklearn
    ENTITY_SPEC_CLASS = ModelSpecSklearn
    ENTITY_SPEC_VALIDATOR = ModelValidatorSklearn
    ENTITY_STATUS_CLASS = ModelStatusSklearn
    ENTITY_KIND = EntityKinds.MODEL_SKLEARN.value
