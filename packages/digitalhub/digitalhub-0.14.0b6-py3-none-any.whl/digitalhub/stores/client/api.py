# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.client.builder import client_builder

if typing.TYPE_CHECKING:
    from digitalhub.stores.client.dhcore.client import ClientDHCore
    from digitalhub.stores.client.local.client import ClientLocal


def get_client(local: bool = False) -> ClientLocal | ClientDHCore:
    """
    Wrapper around ClientBuilder.build.

    Parameters
    ----------
    local : bool, default False
        Whether to create a local client or not. If True, creates a
        ClientLocal instance that operates in-memory. If False, creates
        a ClientDHCore instance that communicates with a remote backend.

    Returns
    -------
    ClientLocal | ClientDHCore
        The client instance.
    """
    return client_builder.build(local)
