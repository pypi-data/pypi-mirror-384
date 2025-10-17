# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Signature(BaseModel):
    """
    MLFlow model signature.
    """

    inputs: Optional[str] = None
    outputs: Optional[str] = None
    params: Optional[str] = None

    def to_dict(self):
        return self.model_dump()


class Dataset(BaseModel):
    """
    MLFlow model dataset.
    """

    name: Optional[str] = None
    digest: Optional[str] = None
    profile: Optional[str] = None
    dataset_schema: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None

    def to_dict(self):
        return self.model_dump()
