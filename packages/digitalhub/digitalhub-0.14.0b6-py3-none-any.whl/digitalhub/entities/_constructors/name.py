# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import random

from pydantic import BaseModel, Field

from digitalhub.entities._constructors._resources import ADJECTIVES, ANIMALS

NAME_REGEX = r"^[a-zA-Z0-9._+-]+$"


class NameValidator(BaseModel):
    """
    Validate name format.
    """

    name: str = Field(min_length=1, max_length=256, pattern=NAME_REGEX)


def build_name(name: str) -> str:
    """
    Build name.

    Parameters
    ----------
    name : str
        The name.

    Returns
    -------
    str
        The name.
    """
    NameValidator(name=name)
    return name


def random_name() -> str:
    """
    Generate a random name.

    Returns
    -------
    str
        The random name.
    """
    adjective = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    return f"{adjective}-{animal}"
