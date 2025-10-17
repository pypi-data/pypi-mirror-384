# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class VolumeType(Enum):
    """
    Volume type.
    """

    PERSISTENT_VOLUME_CLAIM = "persistent_volume_claim"
    EMPTY_DIR = "empty_dir"
    EPHEMERAL = "ephemeral"
    SHARED_VOLUME = "shared_volume"


class SpecEmptyDir(BaseModel):
    """
    Spec empty dir model.
    """

    size_limit: Optional[str] = None

    medium: Optional[str] = None


class SpecPVC(BaseModel):
    """
    Spec PVC model.
    """

    size: Optional[str] = None


class SpecEphemeral(BaseModel):
    """
    Ephemeral volume model.
    """

    size: Optional[str] = None


class SharedVolumeSpec(BaseModel):
    """
    Shared volume spec model.
    """

    size: Optional[str] = None


class Volume(BaseModel):
    """
    Volume model.
    """

    model_config = ConfigDict(use_enum_values=True)

    volume_type: VolumeType
    """Volume type."""

    name: str
    """Volume name."""

    mount_path: str
    """Volume mount path inside the container."""

    spec: Optional[Union[SpecEmptyDir, SpecPVC, SpecEphemeral, SharedVolumeSpec]] = None
    """Volume spec."""


class NodeSelector(BaseModel):
    """
    NodeSelector model.
    """

    key: str
    """Node selector key."""

    value: str
    """Node selector value."""


class ResourceItem(BaseModel):
    """
    Resource item model.
    """

    requests: str = Field(default=None, pattern=r"[\d]+|^([0-9])+([a-zA-Z])+$")
    """Resource requests."""

    limits: str = Field(default=None, pattern=r"[\d]+|^([0-9])+([a-zA-Z])+$")
    """Resource limits."""


class Resource(BaseModel):
    """
    Resource model.
    """

    cpu: Optional[ResourceItem] = None
    """CPU resource model."""

    mem: Optional[ResourceItem] = None
    """Memory resource model."""

    gpu: Optional[ResourceItem] = None
    """GPU resource model."""


class Env(BaseModel):
    """
    Env variable model.
    """

    name: str
    """Env variable name."""

    value: str
    """Env variable value."""


class Toleration(BaseModel):
    """
    Toleration model.
    """

    key: Optional[str] = None
    """Toleration key."""

    operator: Optional[str] = None
    """Toleration operator."""

    value: Optional[str] = None
    """Toleration value."""

    effect: Optional[str] = None
    """Toleration effect."""

    toleration_seconds: Optional[int] = None
    """Toleration seconds."""


class V1NodeSelectorRequirement(BaseModel):
    key: str
    operator: str
    values: Optional[list[str]] = None


class V1NodeSelectorTerm(BaseModel):
    match_expressions: Optional[list[V1NodeSelectorRequirement]] = None
    match_fields: Optional[list[V1NodeSelectorRequirement]] = None


class V1NodeSelector(BaseModel):
    node_selector_terms: list[V1NodeSelectorTerm]


class V1PreferredSchedulingTerm(BaseModel):
    preference: V1NodeSelector
    weight: int


class V1LabelSelectorRequirement(BaseModel):
    key: str
    operator: str
    values: Optional[list[str]] = None


class V1LabelSelector(BaseModel):
    match_expressions: Optional[list[V1LabelSelectorRequirement]] = None
    match_labels: Optional[dict[str, str]] = None


class V1PodAffinityTerm(BaseModel):
    label_selector: Optional[V1LabelSelector] = None
    match_label_keys: Optional[list[str]] = None
    mismatch_label_keys: Optional[list[str]] = None
    namespace_selector: Optional[V1LabelSelector] = None
    namespaces: Optional[list[str]] = None
    topology_key: Optional[str] = None


class V1WeightedPodAffinityTerm(BaseModel):
    pod_affinity_term: V1PodAffinityTerm
    weight: int


class V1NodeAffinity(BaseModel):
    preferred_during_scheduling_ignored_during_execution: Optional[list[V1PreferredSchedulingTerm]] = None
    required_during_scheduling_ignored_during_execution: Optional[V1NodeSelector] = None


class V1PodAffinity(BaseModel):
    preferred_during_scheduling_ignored_during_execution: Optional[list[V1WeightedPodAffinityTerm]] = None
    required_during_scheduling_ignored_during_execution: Optional[list[V1PodAffinityTerm]] = None


class V1PodAntiAffinity(BaseModel):
    preferred_during_scheduling_ignored_during_execution: Optional[list[V1WeightedPodAffinityTerm]] = None
    required_during_scheduling_ignored_during_execution: Optional[list[V1PodAffinityTerm]] = None


class Affinity(BaseModel):
    """
    Affinity model.
    """

    node_affinity: Optional[V1NodeAffinity] = None
    """Node affinity."""

    pod_affinity: Optional[V1PodAffinity] = None
    """Pod affinity."""

    pod_anti_affinity: Optional[V1PodAntiAffinity] = None
    """Pod anti affinity."""


class K8s(BaseModel):
    """
    Kubernetes resource model.
    """

    node_selector: Optional[list[NodeSelector]] = None
    """Node selector."""

    volumes: Optional[list[Volume]] = None
    """List of volumes."""

    resources: Optional[Resource] = None
    """Resources restrictions."""

    affinity: Optional[Affinity] = None
    """Affinity."""

    tolerations: Optional[list[Toleration]] = None
    """Tolerations."""

    envs: Optional[list[Env]] = None
    """Env variables."""

    secrets: Optional[list[str]] = None
    """List of secret names."""

    profile: Optional[str] = None
    """Profile template."""

    runtime_class: Optional[str] = None
    """Runtime class name."""

    priority_class: Optional[str] = None
    """Priority class."""


class CorePort(BaseModel):
    """
    Port mapper model.
    """

    port: int
    target_port: int


class CoreServiceType(Enum):
    """
    CoreServiceType enum.
    """

    EXTERNAL_NAME = "ExternalName"
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


class CorePullPolicy(Enum):
    """
    CorePullPolicy enum.
    """

    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"
