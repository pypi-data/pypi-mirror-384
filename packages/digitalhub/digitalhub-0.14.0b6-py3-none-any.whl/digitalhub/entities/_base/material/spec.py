# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator


class MaterialSpec(Spec):
    """
    Material specifications.class.
    """

    def __init__(self, path: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = path


class MaterialValidator(SpecValidator):
    """
    Material parameters class.
    """

    path: str
    """Target path to file(s)"""
