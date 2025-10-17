# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

from pydantic import Field

from digitalhub.entities.model._base.spec import ModelSpec, ModelValidator
from digitalhub.entities.model.mlflow.models import Dataset, Signature


class ModelSpecMlflow(ModelSpec):
    """
    ModelSpecMlflow specifications.
    """

    def __init__(
        self,
        path: str,
        framework: str | None = None,
        algorithm: str | None = None,
        parameters: dict | None = None,
        flavor: str | None = None,
        model_config: dict | None = None,
        input_datasets: list[Dataset] | None = None,
        signature: Signature | None = None,
    ) -> None:
        super().__init__(path, framework, algorithm, parameters)
        self.flavor = flavor
        self.model_config = model_config
        self.input_datasets = input_datasets
        self.signature = signature


class ModelValidatorMlflow(ModelValidator):
    """
    ModelValidatorMlflow validator.
    """

    flavor: Optional[str] = None
    """Mlflow model flavor."""

    placeholder_cfg_: dict = Field(default=None, alias="model_config")
    """Mlflow model config."""

    input_datasets: Optional[list[Dataset]] = None
    """Mlflow input datasets."""

    signature: Optional[Signature] = None
    """Mlflow model signature."""
