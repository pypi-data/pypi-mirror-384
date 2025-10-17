# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.credentials.handler import creds_handler


def set_current_profile(environment: str) -> None:
    """
    Set the current credentials profile.

    Parameters
    ----------
    environment : str
        Name of the credentials profile to set.
    """
    creds_handler.set_current_profile(environment)


def get_current_profile() -> str:
    """
    Get the name of the current credentials profile.

    Returns
    -------
    str
        Name of the current credentials profile.
    """
    return creds_handler.get_current_profile()
