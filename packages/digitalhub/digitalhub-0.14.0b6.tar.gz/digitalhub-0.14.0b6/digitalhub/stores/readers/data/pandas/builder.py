# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.readers.data._base.builder import ReaderBuilder
from digitalhub.stores.readers.data.pandas.reader import DataframeReaderPandas


class ReaderBuilderPandas(ReaderBuilder):
    """
    Pandas reader builder.
    """

    ENGINE = "pandas"
    DATAFRAME_CLASS = "pandas.core.frame.DataFrame"

    def build(self, **kwargs) -> DataframeReaderPandas:
        """
        Build reader object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        DataframeReaderPandas
            Pandas reader object.
        """
        return DataframeReaderPandas(**kwargs)
