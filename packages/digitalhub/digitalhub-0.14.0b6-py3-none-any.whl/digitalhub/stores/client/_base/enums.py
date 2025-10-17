# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class ApiCategories(Enum):
    """
    API categories.
    """

    BASE = "base"
    CONTEXT = "context"


class BackendOperations(Enum):
    """
    Backend operations.
    """

    CREATE = "create"
    READ = "read"
    READ_ALL_VERSIONS = "read_all_versions"
    UPDATE = "update"
    DELETE = "delete"
    DELETE_ALL_VERSIONS = "delete_all_versions"
    LIST = "list"
    LIST_FIRST = "list_first"
    STOP = "stop"
    RESUME = "resume"
    DATA = "data"
    FILES = "files"
    LOGS = "logs"
    SEARCH = "search"
    SHARE = "share"
    METRICS = "metrics"
