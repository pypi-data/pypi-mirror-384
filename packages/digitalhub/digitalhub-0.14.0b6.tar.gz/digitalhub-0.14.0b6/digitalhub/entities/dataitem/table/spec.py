# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities.dataitem._base.spec import DataitemSpec, DataitemValidator
from digitalhub.entities.dataitem.table.models import TableSchema


class DataitemSpecTable(DataitemSpec):
    """
    DataitemSpecTable specifications.
    """

    def __init__(self, path: str, schema: dict | None = None) -> None:
        super().__init__(path)
        self.schema = schema


class DataitemValidatorTable(DataitemValidator):
    """
    DataitemValidatorTable validator.
    """

    schema_: TableSchema = Field(default=None, alias="schema")
    """The schema of the dataitem in table schema format."""
