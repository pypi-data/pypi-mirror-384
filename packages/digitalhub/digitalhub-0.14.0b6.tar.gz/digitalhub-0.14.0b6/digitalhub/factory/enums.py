# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class FactoryEnum(Enum):
    """
    Enumeration for factory.
    """

    RGX_RUNTIMES = r"digitalhub_runtime_.*"
    REG_ENTITIES = "digitalhub.entities.builders"
    REG_ENTITIES_VAR = "entity_builders"
    REG_RUNTIME_VAR = "runtime_builders"
