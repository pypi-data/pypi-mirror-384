# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.dataitem._base.entity import Dataitem

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.dataitem.iceberg.spec import DataitemSpecIceberg
    from digitalhub.entities.dataitem.iceberg.status import DataitemStatusIceberg


class DataitemIceberg(Dataitem):
    """
    DataitemIceberg class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: DataitemSpecIceberg,
        status: DataitemStatusIceberg,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: DataitemSpecIceberg
        self.status: DataitemStatusIceberg
