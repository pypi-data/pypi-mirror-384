# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

from digitalhub.entities._base.entity.spec import Spec, SpecValidator
from digitalhub.entities.project._base.models import ProfileConfig


class ProjectSpec(Spec):
    """
    ProjectSpec specifications.
    """

    def __init__(
        self,
        context: str | None = None,
        functions: list | None = None,
        artifacts: list | None = None,
        workflows: list | None = None,
        dataitems: list | None = None,
        models: list | None = None,
        config: dict | None = None,
        **kwargs,
    ) -> None:
        self.context = context if context is not None else "./"
        self.functions = functions if functions is not None else []
        self.artifacts = artifacts if artifacts is not None else []
        self.workflows = workflows if workflows is not None else []
        self.dataitems = dataitems if dataitems is not None else []
        self.models = models if models is not None else []
        self.config = config if config is not None else {}


class ProjectValidator(SpecValidator):
    """
    ProjectValidator validator.
    """

    context: Optional[str] = None
    """The project's context."""

    functions: Optional[list] = None
    """List of project's functions."""

    artifacts: Optional[list] = None
    """List of project's artifacts."""

    workflows: Optional[list] = None
    """List of project's workflows."""

    dataitems: Optional[list] = None
    """List of project's dataitems."""

    models: Optional[list] = None
    """List of project's models."""

    config: Optional[ProfileConfig] = None
    """Project's config."""
