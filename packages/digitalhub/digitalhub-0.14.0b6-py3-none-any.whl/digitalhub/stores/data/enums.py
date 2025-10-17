# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class StoreEnv(Enum):
    """
    Environment variables for data stores.
    """

    DEFAULT_FILES_STORE = "DHCORE_DEFAULT_FILES_STORE"
