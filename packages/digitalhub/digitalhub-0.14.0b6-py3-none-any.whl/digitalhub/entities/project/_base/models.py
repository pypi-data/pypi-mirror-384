# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

_DEFAULT_FILES_STORE = "s3://datalake"


class ProfileConfig(BaseModel):
    """
    Configuration profiles.
    """

    default_files_store: Optional[str] = _DEFAULT_FILES_STORE

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)
