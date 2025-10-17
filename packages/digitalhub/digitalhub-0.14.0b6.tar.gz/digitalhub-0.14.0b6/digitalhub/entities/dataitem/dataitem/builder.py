# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem.dataitem.entity import DataitemDataitem
from digitalhub.entities.dataitem.dataitem.spec import DataitemSpecDataitem, DataitemValidatorDataitem
from digitalhub.entities.dataitem.dataitem.status import DataitemStatusDataitem


class DataitemDataitemBuilder(DataitemBuilder):
    """
    DataitemDataitem builder.
    """

    ENTITY_CLASS = DataitemDataitem
    ENTITY_SPEC_CLASS = DataitemSpecDataitem
    ENTITY_SPEC_VALIDATOR = DataitemValidatorDataitem
    ENTITY_STATUS_CLASS = DataitemStatusDataitem
    ENTITY_KIND = EntityKinds.DATAITEM_DATAITEM.value
