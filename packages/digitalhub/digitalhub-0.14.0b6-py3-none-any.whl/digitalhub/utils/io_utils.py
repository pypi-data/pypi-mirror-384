# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

import yaml

##############################
# Writers
##############################


def write_yaml(filepath: str | Path, obj: dict | list[dict]) -> None:
    """
    Write a dict or a list of dicts to a YAML file.

    Parameters
    ----------
    filepath : str or Path
        The YAML file path to write.
    obj : dict or list of dict
        The dict or list of dicts to write.
    """
    if isinstance(obj, list):
        with open(filepath, "w", encoding="utf-8") as out_file:
            yaml.dump_all(obj, out_file, sort_keys=False, default_flow_style=False)
    else:
        with open(filepath, "w", encoding="utf-8") as out_file:
            yaml.dump(obj, out_file, sort_keys=False)


def write_text(filepath: Path, text: str) -> None:
    """
    Write text to a file.

    Parameters
    ----------
    filepath : Path
        The file path to write.
    text : str
        The text to write.
    """
    filepath.write_text(text, encoding="utf-8")


##############################
# Readers
##############################


class NoDatesSafeLoader(yaml.SafeLoader):
    """
    Loader implementation to exclude implicit resolvers for YAML timestamps.

    Taken from https://stackoverflow.com/a/37958106
    """

    @classmethod
    def remove_implicit_resolver(cls, tag_to_remove: str) -> None:
        """
        Remove implicit resolvers for a particular tag.

        Takes care not to modify resolvers in super classes.
        We want to load datetimes as strings, not dates, because we
        go on to serialize as JSON which doesn't have the advanced types
        of YAML, and leads to incompatibilities down the track.

        Parameters
        ----------
        tag_to_remove : str
            The tag to remove.
        """
        if "yaml_implicit_resolvers" not in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [
                (tag, regexp) for tag, regexp in mappings if tag != tag_to_remove
            ]


NoDatesSafeLoader.remove_implicit_resolver("tag:yaml.org,2002:timestamp")


def read_yaml(filepath: str | Path) -> dict | list[dict]:
    """
    Read a YAML file and return its content as a dict or a list of dicts.

    Parameters
    ----------
    filepath : str or Path
        The YAML file path to read.

    Returns
    -------
    dict or list of dict
        The YAML file content.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as in_file:
            data = yaml.load(in_file, Loader=NoDatesSafeLoader)

    # If yaml contains multiple documents
    except yaml.composer.ComposerError:
        with open(filepath, "r", encoding="utf-8") as in_file:
            data = list(yaml.load_all(in_file, Loader=NoDatesSafeLoader))
    return data


def read_text(filepath: str | Path) -> str:
    """
    Read a file and return its text content.

    Parameters
    ----------
    filepath : str or Path
        The file path to read.

    Returns
    -------
    str
        The file content as a string.
    """
    return Path(filepath).read_text(encoding="utf-8")
