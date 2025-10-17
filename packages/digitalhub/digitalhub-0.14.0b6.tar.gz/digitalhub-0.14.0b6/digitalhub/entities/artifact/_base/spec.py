# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.material.spec import MaterialSpec, MaterialValidator


class ArtifactSpec(MaterialSpec):
    """
    ArtifactSpec specifications.
    """


class ArtifactValidator(MaterialValidator):
    """
    ArtifactValidator validator.
    """
