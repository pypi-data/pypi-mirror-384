# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class FileExtensions(Enum):
    """
    Supported file extensions.
    """

    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"
    EXCEL_OLD = "xls"
    EXCEL = "xlsx"
    TXT = "txt"
    FILE = "file"
