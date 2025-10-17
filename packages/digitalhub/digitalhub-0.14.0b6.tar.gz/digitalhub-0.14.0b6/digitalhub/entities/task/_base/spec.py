# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator
from digitalhub.entities.task._base.models import K8s


class TaskSpec(Spec):
    """TaskSpec specifications."""


class TaskSpecFunction(TaskSpec):
    """TaskSpecFunction specifications."""

    def __init__(
        self,
        function: str,
        node_selector: list[dict] | None = None,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        affinity: dict | None = None,
        tolerations: list[dict] | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        runtime_class: str | None = None,
        priority_class: str | None = None,
        **kwargs,
    ) -> None:
        self.function = function
        self.node_selector = node_selector
        self.volumes = volumes
        self.resources = resources
        self.affinity = affinity
        self.tolerations = tolerations
        self.envs = envs
        self.secrets = secrets
        self.profile = profile
        self.runtime_class = runtime_class
        self.priority_class = priority_class


class TaskSpecWorkflow(TaskSpec):
    """TaskSpecWorkflow specifications."""

    def __init__(
        self,
        workflow: str,
        node_selector: list[dict] | None = None,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        affinity: dict | None = None,
        tolerations: list[dict] | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        runtime_class: str | None = None,
        priority_class: str | None = None,
        **kwargs,
    ) -> None:
        self.workflow = workflow
        self.node_selector = node_selector
        self.volumes = volumes
        self.resources = resources
        self.affinity = affinity
        self.tolerations = tolerations
        self.envs = envs
        self.secrets = secrets
        self.profile = profile
        self.runtime_class = runtime_class
        self.priority_class = priority_class


class TaskValidator(SpecValidator):
    """
    TaskValidator validator.
    """


class TaskValidatorFunction(TaskValidator, K8s):
    """
    TaskValidatorFunction validator.
    """

    function: str


class TaskValidatorWorkflow(TaskValidator, K8s):
    """
    TaskValidatorWorkflow validator.
    """

    workflow: str
