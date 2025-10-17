# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

from digitalhub.entities._base.entity.spec import Spec, SpecValidator


class SecretSpec(Spec):
    """
    SecretSpec specifications.
    """

    def __init__(self, path: str | None = None, provider: str | None = None, **kwargs) -> None:
        """
        Constructor.

        Parameters
        ----------
        path : str
            Path to the secret.
        provider : str
            Provider of the secret.
        """
        self.path = path
        self.provider = provider


class SecretValidator(SpecValidator):
    """
    SecretValidator validator.
    """

    path: Optional[str] = None
    """Path to the secret."""

    provider: Optional[str] = None
    """Provider of the secret."""
