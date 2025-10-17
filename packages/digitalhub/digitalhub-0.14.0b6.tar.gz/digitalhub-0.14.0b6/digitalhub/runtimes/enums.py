# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class RuntimeEnvVar(Enum):
    """
    Environment variables used by runtime execution environments.

    These variables are automatically set in the runtime context
    and can be accessed during task execution.

    Values
    ------
    PROJECT : str
        Environment variable name for the current project identifier
    RUN_ID : str
        Environment variable name for the current run identifier
    """

    PROJECT = "PROJECT_NAME"
    RUN_ID = "RUN_ID"
