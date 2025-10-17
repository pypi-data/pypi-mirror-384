# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod

from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.stores.readers.data._base.reader import DataframeReader


class ReaderBuilder:
    ENGINE = None
    DATAFRAME_CLASS = None

    def __init__(self):
        if self.ENGINE is None:
            raise BuilderError("ENGINE must be set.")
        if self.DATAFRAME_CLASS is None:
            raise BuilderError("DATAFRAME_CLASS must be set.")

    @abstractmethod
    def build(self, **kwargs) -> DataframeReader:
        """
        Build reader object.
        """
