# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.stores.readers.data._base.builder import ReaderBuilder
    from digitalhub.stores.readers.data._base.reader import DataframeReader


class ReaderFactory:
    """
    Reader factory class.
    """

    def __init__(self) -> None:
        self._engine_builders: dict[str, ReaderBuilder] = None
        self._dataframe_builders: dict[str, ReaderBuilder] = None
        self._default: str = None

    def add_builder(self, engine: str, dataframe: str, builder: ReaderBuilder) -> None:
        """
        Add a builder to the factory.

        Parameters
        ----------
        name : str
            Reader name.
        builder : DataframeReader
            Builder object.
        """
        if self._engine_builders is None:
            self._engine_builders = {}
        if engine in self._engine_builders:
            raise BuilderError(f"Builder for engine '{engine}' already exists.")
        self._engine_builders[engine] = builder

        if self._dataframe_builders is None:
            self._dataframe_builders = {}
        if dataframe in self._dataframe_builders:
            raise BuilderError(f"Builder for dataframe '{dataframe}' already exists.")
        self._dataframe_builders[dataframe] = builder

    def build(self, engine: str | None = None, dataframe: str | None = None, **kwargs) -> DataframeReader:
        """
        Build reader object.

        Parameters
        ----------
        engine : str | None
            Engine name.
        dataframe : str | None
            Dataframe name.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        DataframeReader
            Reader object.
        """
        if (engine is None) == (dataframe is None):
            raise BuilderError("Either engine or dataframe must be provided.")
        if engine is not None:
            return self._engine_builders[engine].build(**kwargs)
        return self._dataframe_builders[dataframe].build(**kwargs)

    def list_supported_engines(self) -> list[str]:
        """
        List supported engines.

        Returns
        -------
        list[str]
            List of supported engines.
        """
        return list(self._engine_builders.keys())

    def list_supported_dataframes(self) -> list[str]:
        """
        List supported dataframes.

        Returns
        -------
        list[str]
            List of supported dataframes.
        """
        return list(self._dataframe_builders.keys())

    def set_default(self, engine: str) -> None:
        """
        Set default engine.

        Parameters
        ----------
        engine : str
            Engine name.
        """
        if engine not in self._engine_builders:
            raise BuilderError(f"Engine {engine} not found.")
        self._default = engine

    def get_default(self) -> str:
        """
        Get default engine.

        Returns
        -------
        str
            Default engine.
        """
        if self._default is None:
            raise BuilderError("No default engine set.")
        return self._default


factory = ReaderFactory()

try:
    from digitalhub.stores.readers.data.pandas.builder import ReaderBuilderPandas

    factory.add_builder(
        ReaderBuilderPandas.ENGINE,
        ReaderBuilderPandas.DATAFRAME_CLASS,
        ReaderBuilderPandas(),
    )
    factory.set_default(ReaderBuilderPandas.ENGINE)

except ImportError:
    pass
