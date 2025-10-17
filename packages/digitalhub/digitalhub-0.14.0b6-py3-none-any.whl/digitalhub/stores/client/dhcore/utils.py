# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.client.api import get_client

if typing.TYPE_CHECKING:
    pass


def refresh_token() -> None:
    """
    Refresh the current OAuth2 access token.

    Uses the refresh token stored in client configuration to obtain a new
    access token. Requires OAuth2 authentication configuration.


    Raises
    ------
    ClientError
        If client not properly configured or token refresh fails.
    """
    get_client(local=False).refresh_token()
