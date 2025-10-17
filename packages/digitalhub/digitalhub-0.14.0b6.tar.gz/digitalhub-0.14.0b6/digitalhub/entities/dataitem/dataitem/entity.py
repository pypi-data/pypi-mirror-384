# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.dataitem._base.entity import Dataitem

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.dataitem.dataitem.spec import DataitemSpecDataitem
    from digitalhub.entities.dataitem.dataitem.status import DataitemStatusDataitem


class DataitemDataitem(Dataitem):
    """
    DataitemDataitem class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: DataitemSpecDataitem,
        status: DataitemStatusDataitem,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: DataitemSpecDataitem
        self.status: DataitemStatusDataitem
