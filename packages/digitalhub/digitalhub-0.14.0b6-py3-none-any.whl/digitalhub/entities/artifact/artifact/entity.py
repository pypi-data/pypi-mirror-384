# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.artifact._base.entity import Artifact

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.artifact.artifact.spec import ArtifactSpecArtifact
    from digitalhub.entities.artifact.artifact.status import ArtifactStatusArtifact


class ArtifactArtifact(Artifact):
    """
    ArtifactArtifact class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: ArtifactSpecArtifact,
        status: ArtifactStatusArtifact,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: ArtifactSpecArtifact
        self.status: ArtifactStatusArtifact
