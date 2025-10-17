# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class EntityTypes(Enum):
    """
    Entity types.
    """

    PROJECT = "project"
    ARTIFACT = "artifact"
    DATAITEM = "dataitem"
    MODEL = "model"
    SECRET = "secret"
    FUNCTION = "function"
    WORKFLOW = "workflow"
    TASK = "task"
    RUN = "run"
    TRIGGER = "trigger"


class Relationship(Enum):
    """
    Relationship enumeration.
    """

    PRODUCEDBY = "produced_by"
    CONSUMES = "consumes"
    RUN_OF = "run_of"
    STEP_OF = "step_of"


class State(Enum):
    """
    State enumeration.
    """

    BUILT = "BUILT"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    CREATED = "CREATED"
    CREATING = "CREATING"
    DELETED = "DELETED"
    DELETING = "DELETING"
    ERROR = "ERROR"
    FSM_ERROR = "FSM_ERROR"
    IDLE = "IDLE"
    NONE = "NONE"
    ONLINE = "ONLINE"
    PENDING = "PENDING"
    READY = "READY"
    RESUME = "RESUME"
    RUN_ERROR = "RUN_ERROR"
    RUNNING = "RUNNING"
    STOP = "STOP"
    STOPPED = "STOPPED"
    SUCCESS = "SUCCESS"
    UNKNOWN = "UNKNOWN"
    UPLOADING = "UPLOADING"


class EntityKinds(Enum):
    """
    Entity kinds.
    """

    PROJECT_PROJECT = "project"
    ARTIFACT_ARTIFACT = "artifact"
    DATAITEM_DATAITEM = "dataitem"
    DATAITEM_TABLE = "table"
    DATAITEM_ICEBERG = "iceberg"
    MODEL_MODEL = "model"
    MODEL_MLFLOW = "mlflow"
    MODEL_HUGGINGFACE = "huggingface"
    MODEL_SKLEARN = "sklearn"
    SECRET_SECRET = "secret"
    TRIGGER_SCHEDULER = "scheduler"
    TRIGGER_LIFECYCLE = "lifecycle"
