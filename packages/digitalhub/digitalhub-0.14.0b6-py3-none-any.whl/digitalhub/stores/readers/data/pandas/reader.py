# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from io import BytesIO
from typing import IO, Any

import numpy as np
import pandas as pd
from pandas.errors import ParserError

from digitalhub.entities.dataitem.table.utils import check_preview_size, finalize_preview, prepare_data, prepare_preview
from digitalhub.stores.readers.data._base.reader import DataframeReader
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.exceptions import ReaderError
from digitalhub.utils.generic_utils import CustomJsonEncoder


class DataframeReaderPandas(DataframeReader):
    """
    Pandas reader class.
    """

    ##############################
    # Read methods
    ##############################

    def read_df(self, path_or_buffer: str | IO, extension: str, **kwargs) -> pd.DataFrame:
        """
        Read DataFrame from path or buffer.

        Parameters
        ----------
        path_or_buffer : str | IO
            Path or buffer to read DataFrame from.
        extension : str
            Extension of the file.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        pd.DataFrame
            Pandas DataFrame.
        """
        if extension == FileExtensions.CSV.value:
            return pd.read_csv(path_or_buffer, **kwargs)
        if extension == FileExtensions.PARQUET.value:
            return pd.read_parquet(path_or_buffer, **kwargs)
        if extension == FileExtensions.JSON.value:
            return pd.read_json(path_or_buffer, **kwargs)
        if extension in (FileExtensions.EXCEL.value, FileExtensions.EXCEL_OLD.value):
            return pd.read_excel(path_or_buffer, **kwargs)
        if extension in (FileExtensions.TXT.value, FileExtensions.FILE.value):
            try:
                return self.read_df(path_or_buffer, FileExtensions.CSV.value, **kwargs)
            except ParserError:
                raise ReaderError(f"Unable to read from {path_or_buffer}.")
        else:
            raise ReaderError(f"Unsupported extension '{extension}' for reading.")

    def read_table(self, sql: str, engine: Any, **kwargs) -> pd.DataFrame:
        """
        Read table from db.

        Parameters
        ----------
        sql : str
            SQL query.
        engine : Any
            SQL Engine.
        **kwargs
            Keyword arguments.

        Returns
        -------
        pd.DataFrame
            Pandas DataFrame.
        """
        return pd.read_sql(sql=sql, con=engine, **kwargs)

    ##############################
    # Write methods
    ##############################

    def write_df(
        self,
        df: pd.DataFrame,
        dst: str | BytesIO,
        extension: str | None = None,
        **kwargs,
    ) -> None:
        """
        Write DataFrame as parquet.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to write.
        dst : str | BytesIO
            The destination of the dataframe.
        **kwargs : dict
            Keyword arguments.
        """
        if extension == FileExtensions.CSV.value:
            return self.write_csv(df, dst, **kwargs)
        if extension == FileExtensions.PARQUET.value:
            return self.write_parquet(df, dst, **kwargs)
        raise ReaderError(f"Unsupported extension '{extension}' for writing.")

    @staticmethod
    def write_csv(df: pd.DataFrame, dst: str | BytesIO, **kwargs) -> None:
        """
        Write DataFrame as csv.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to write.
        dst : str | BytesIO
            The destination of the dataframe.
        **kwargs : dict
            Keyword arguments.
        """
        if "index" not in kwargs:
            kwargs["index"] = False
        df.to_csv(dst, **kwargs)

    @staticmethod
    def write_parquet(df: pd.DataFrame, dst: str | BytesIO, **kwargs) -> None:
        """
        Write DataFrame as parquet.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to write.
        dst : str | BytesIO
            The destination of the dataframe.
        **kwargs : dict
            Keyword arguments.
        """
        if "index" not in kwargs:
            kwargs["index"] = False
        df.to_parquet(dst, **kwargs)

    @staticmethod
    def write_table(df: pd.DataFrame, table: str, engine: Any, schema: str | None = None, **kwargs) -> None:
        """
        Write DataFrame as table.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to write.
        table : str
            The destination table.
        engine : Any
            SQL Engine.
        schema : str
            The destination schema.
        **kwargs : dict
            Keyword arguments.
        """
        if "index" not in kwargs:
            kwargs["index"] = False
        df.to_sql(table, engine, schema=schema, **kwargs)

    ##############################
    # Utils
    ##############################

    @staticmethod
    def concat_dfs(dfs: list[pd.DataFrame]) -> pd.DataFrame:
        """
        Concatenate a list of DataFrames.

        Parameters
        ----------
        dfs : list[pd.DataFrame]
            The DataFrames to concatenate.

        Returns
        -------
        pd.DataFrame
            The concatenated DataFrame.
        """
        return pd.concat(dfs, ignore_index=True)

    @staticmethod
    def get_schema(df: pd.DataFrame) -> Any:
        """
        Get schema.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe.

        Returns
        -------
        Any
            The schema.
        """
        schema = {"fields": []}

        for column_name, dtype in df.dtypes.items():
            field = {"name": str(column_name), "type": ""}

            if pd.api.types.is_integer_dtype(dtype):
                field["type"] = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                field["type"] = "number"
            elif pd.api.types.is_bool_dtype(dtype):
                field["type"] = "boolean"
            elif pd.api.types.is_string_dtype(dtype):
                field["type"] = "string"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                field["type"] = "datetime"
            else:
                field["type"] = "any"

            schema["fields"].append(field)

        return schema

    @staticmethod
    def get_preview(df: pd.DataFrame) -> dict:
        """
        Get preview.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe.

        Returns
        -------
        Any
            The preview.
        """
        columns = [str(col) for col, _ in df.dtypes.items()]
        head = df.head(10).replace({np.nan: None})
        data = head.values.tolist()
        prepared_data = prepare_data(data)
        preview = prepare_preview(columns, prepared_data)
        finalizes = finalize_preview(preview, df.shape[0])
        serialized = _serialize_deserialize_preview(finalizes)
        return check_preview_size(serialized)


class PandasJsonEncoder(CustomJsonEncoder):
    """
    JSON pd.Timestamp to ISO format serializer.
    """

    def default(self, obj: Any) -> Any:
        """
        Pandas datetime to ISO format serializer.

        Parameters
        ----------
        obj : Any
            The object to serialize.

        Returns
        -------
        Any
            The serialized object.
        """
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)


def _serialize_deserialize_preview(preview: dict) -> dict:
    """
    Serialize and deserialize preview.

    Parameters
    ----------
    preview : dict
        The preview.

    Returns
    -------
    dict
        The serialized preview.
    """
    return json.loads(json.dumps(preview, cls=PandasJsonEncoder))
