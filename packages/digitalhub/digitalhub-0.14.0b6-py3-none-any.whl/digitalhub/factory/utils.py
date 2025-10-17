# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib
import pkgutil
import re
from types import ModuleType

from digitalhub.factory.enums import FactoryEnum


def import_module(package: str) -> ModuleType:
    """
    Import a module dynamically by package name.

    Parameters
    ----------
    package : str
        The fully qualified package name to import.

    Returns
    -------
    ModuleType
        The imported module object.

    Raises
    ------
    ModuleNotFoundError
        If the specified package cannot be found.
    RuntimeError
        If any other error occurs during import.
    """
    try:
        return importlib.import_module(package)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Package {package} not found.") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred while importing {package}.") from e


def list_runtimes() -> list[str]:
    """
    List all installed DigitalHub runtime packages.

    Scans installed packages for those matching the pattern
    'digitalhub_runtime_*'.

    Returns
    -------
    list of str
        List of runtime package names.

    Raises
    ------
    RuntimeError
        If an error occurs while scanning for runtime packages.
    """
    try:
        runtimes: list[str] = []
        for _, name, _ in pkgutil.iter_modules():
            if re.match(FactoryEnum.RGX_RUNTIMES.value, name):
                runtimes.append(name)
        return runtimes
    except Exception as e:
        raise RuntimeError("Error listing installed runtimes.") from e
