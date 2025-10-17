# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem.iceberg.entity import DataitemIceberg
from digitalhub.entities.dataitem.iceberg.spec import DataitemSpecIceberg, DataitemValidatorIceberg
from digitalhub.entities.dataitem.iceberg.status import DataitemStatusIceberg


class DataitemIcebergBuilder(DataitemBuilder):
    """
    DataitemIceberg builder.
    """

    ENTITY_CLASS = DataitemIceberg
    ENTITY_SPEC_CLASS = DataitemSpecIceberg
    ENTITY_SPEC_VALIDATOR = DataitemValidatorIceberg
    ENTITY_STATUS_CLASS = DataitemStatusIceberg
    ENTITY_KIND = EntityKinds.DATAITEM_ICEBERG.value
