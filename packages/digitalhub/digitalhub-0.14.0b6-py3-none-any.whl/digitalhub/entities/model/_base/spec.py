# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

from digitalhub.entities._base.material.spec import MaterialSpec, MaterialValidator


class ModelSpec(MaterialSpec):
    """
    ModelSpec specifications.
    """

    def __init__(
        self,
        path: str,
        framework: str | None = None,
        algorithm: str | None = None,
        parameters: dict | None = None,
    ) -> None:
        super().__init__(path)
        self.framework = framework
        self.algorithm = algorithm
        self.parameters = parameters


class ModelValidator(MaterialValidator):
    """
    ModelValidator validator.
    """

    framework: Optional[str] = None
    """Model framework (e.g. 'pytorch')."""

    algorithm: Optional[str] = None
    """Model algorithm (e.g. 'resnet')."""

    parameters: Optional[dict] = None
    """Model validator."""
