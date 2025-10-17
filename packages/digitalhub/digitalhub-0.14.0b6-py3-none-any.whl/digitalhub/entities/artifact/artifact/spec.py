# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

from digitalhub.entities.artifact._base.spec import ArtifactSpec, ArtifactValidator


class ArtifactSpecArtifact(ArtifactSpec):
    """
    ArtifactSpecArtifact specifications.
    """

    def __init__(
        self,
        path: str,
        src_path: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(path, **kwargs)
        self.src_path = src_path


class ArtifactValidatorArtifact(ArtifactValidator):
    """
    ArtifactValidatorArtifact validator.
    """

    src_path: Optional[str] = None
    """Source path of the artifact."""
