# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

from digitalhub.utils.exceptions import ClientError

# File where to write credementials
ENV_FILE = Path.home() / ".dhcore.ini"


def load_file() -> ConfigParser:
    """
    Load the credentials configuration from the .dhcore.ini file.

    Returns
    -------
    ConfigParser
        Parsed configuration file object.

    Raises
    ------
    ClientError
        If the file cannot be read.
    """
    try:
        file = ConfigParser()
        file.read(ENV_FILE)
        return file
    except Exception as e:
        raise ClientError(f"Failed to read env file: {e}")


def load_profile(file: ConfigParser) -> str | None:
    """
    Load the current credentials profile name from the .dhcore.ini file.

    Parameters
    ----------
    file : ConfigParser
        Parsed configuration file object.

    Returns
    -------
    str or None
        Name of the credentials profile, or None if not found.
    """
    try:
        return file["DEFAULT"]["current_environment"]
    except KeyError:
        return


def load_key(file: ConfigParser, profile: str, key: str) -> str | None:
    """
    Load a specific key value from the credentials profile in the
    .dhcore.ini file.

    Parameters
    ----------
    file : ConfigParser
        Parsed configuration file object.
    profile : str
        Name of the credentials profile.
    key : str
        Name of the key to retrieve.

    Returns
    -------
    str or None
        Value of the key, or None if not found.
    """
    try:
        return file[profile][key]
    except KeyError:
        return


def write_config(creds: dict, environment: str) -> None:
    """
    Write credentials to the .dhcore.ini file for the specified environment.
    Overwrites any existing values for that environment.

    Parameters
    ----------
    creds : dict
        Dictionary of credentials to write.
    environment : str
        Name of the credentials profile/environment.


    Raises
    ------
    ClientError
        If the file cannot be written.
    """
    try:
        cfg = load_file()

        sections = cfg.sections()
        if environment not in sections:
            cfg.add_section(environment)

        cfg["DEFAULT"]["current_environment"] = environment
        for k, v in creds.items():
            cfg[environment][k] = str(v)

        ENV_FILE.touch(exist_ok=True)
        with open(ENV_FILE, "w") as inifile:
            cfg.write(inifile)

    except Exception as e:
        raise ClientError(f"Failed to write env file: {e}")


def set_current_profile(environment: str) -> None:
    """
    Set the current credentials profile in the .dhcore.ini file.

    Parameters
    ----------
    environment : str
        Name of the credentials profile to set as current.


    Raises
    ------
    ClientError
        If the file cannot be written.
    """
    try:
        cfg = load_file()
        cfg["DEFAULT"]["current_environment"] = environment
        with open(ENV_FILE, "w") as inifile:
            cfg.write(inifile)

    except Exception as e:
        raise ClientError(f"Failed to write env file: {e}")
