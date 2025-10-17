# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger.lifecycle.entity import TriggerLifecycle
from digitalhub.entities.trigger.lifecycle.spec import TriggerSpecLifecycle, TriggerValidatorLifecycle
from digitalhub.entities.trigger.lifecycle.status import TriggerStatusLifecycle


class TriggerLifecycleBuilder(TriggerBuilder):
    """
    TriggerLifecycle builder.
    """

    ENTITY_CLASS = TriggerLifecycle
    ENTITY_SPEC_CLASS = TriggerSpecLifecycle
    ENTITY_SPEC_VALIDATOR = TriggerValidatorLifecycle
    ENTITY_STATUS_CLASS = TriggerStatusLifecycle
    ENTITY_KIND = EntityKinds.TRIGGER_LIFECYCLE.value
