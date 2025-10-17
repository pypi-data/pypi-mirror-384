# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.utils.generic_utils import dump_json


def prepare_data(data: list[list], columnar: bool = False) -> list[list]:
    """
    Prepare data.

    Parameters
    ----------
    data : list
        Data.
    columnar : bool | None
        If data are arranged in columns. If False, data are arranged in rows.

    Returns
    -------
    list[list]
        Prepared data.
    """
    # Reduce data to 10 rows
    if not columnar:
        if len(data) > 10:
            data = data[:10]
    else:
        data = [d[:10] for d in data]

    # Transpose data if needed
    if not columnar:
        data = list(map(list, list(zip(*data))))

    return data


def prepare_preview(columns: list, data: list[list]) -> list[dict]:
    """
    Get preview.

    Parameters
    ----------
    data : pd.DataFrame
        Data.

    Returns
    -------
    list[dict]
        Preview.
    """
    if len(columns) != len(data):
        raise ValueError("Column names and data must have the same length")
    preview = [{"name": column, "value": values} for column, values in zip(columns, data)]
    return filter_memoryview(preview)


def filter_memoryview(data: list[dict]) -> list[dict]:
    """
    Find memoryview values.

    Parameters
    ----------
    data : list[dict]
        Data.

    Returns
    -------
    list[dict]
        Preview.
    """
    key_to_filter = []
    for i in data:
        if any(isinstance(v, memoryview) for v in i["value"]):
            key_to_filter.append(i["name"])
    for i in key_to_filter:
        data = [d for d in data if d["name"] != i]
    return data


def check_preview_size(preview: dict) -> dict:
    """
    Check preview size. If it's too big, return empty dict.

    Parameters
    ----------
    preview : dict
        Preview.

    Returns
    -------
    dict
        Preview.
    """
    if len(dump_json(preview)) >= 64000:
        return {}
    return preview


def finalize_preview(preview: list[dict] | None = None, rows_count: int | None = None) -> dict:
    """
    Finalize preview.

    Parameters
    ----------
    preview : list[dict]
        Preview.
    rows_count : int
        Row count.

    Returns
    -------
    dict
        Data preview.
    """
    data: dict[str, list[dict] | int] = {}
    if preview is not None:
        data["cols"] = preview
    if rows_count is not None:
        data["rows"] = rows_count
    return data
