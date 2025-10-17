# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class AuthType(Enum):
    """
    Authentication types.
    """

    BASIC = "basic"
    OAUTH2 = "oauth2"
    EXCHANGE = "exchange"
    ACCESS_TOKEN = "access_token_only"
