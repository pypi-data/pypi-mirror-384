# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.data.api import get_store

if typing.TYPE_CHECKING:
    from digitalhub.stores.data.s3.store import S3Client, S3Store
    from digitalhub.stores.data.sql.store import Engine, SqlStore


def get_s3_client() -> S3Client:
    """
    Returns a boto3 S3 client.

    Returns
    -------
    S3Client
        A boto3 S3 client instance.
    """
    store: S3Store = get_store("s3://")
    return store.get_s3_client()


def get_sql_engine(schema: str | None = None) -> Engine:
    """
    Returns a SQLAlchemy engine connected to the database.

    Parameters
    ----------
    schema : str
        The schema to connect to, by default None.

    Returns
    -------
    Engine
        A SQLAlchemy engine instance connected to the database.
    """
    store: SqlStore = get_store("sql://")
    return store.get_engine(schema=schema)
