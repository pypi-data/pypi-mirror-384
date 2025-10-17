# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.context.import_export import ContextEntityImportExportProcessor
from digitalhub.entities._processors.context.material import ContextEntityMaterialProcessor
from digitalhub.entities._processors.context.special_ops import ContextEntitySpecialOpsProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.executable.entity import ExecutableEntity
    from digitalhub.entities._base.material.entity import MaterialEntity
    from digitalhub.entities._base.unversioned.entity import UnversionedEntity


class ContextEntityOperationsProcessor:
    """
    Processor for context entity operations.

    This class handles CRUD operations and other entity management tasks
    for context-level entities (artifacts, functions, workflows, runs, etc.)
    within projects. It manages the full lifecycle of versioned and
    unversioned entities including creation, reading, updating, deletion,
    import/export, and specialized operations like file uploads and metrics.

    Uses composition with specialized processors for different operation types.
    """

    def __init__(self):
        self.crud_processor = ContextEntityCRUDProcessor()
        self.material_processor = ContextEntityMaterialProcessor()
        self.import_export_processor = ContextEntityImportExportProcessor()
        self.special_ops_processor = ContextEntitySpecialOpsProcessor()

    ##############################
    # CRUD context entity
    ##############################

    def create_context_entity(
        self,
        _entity: ContextEntity | None = None,
        **kwargs,
    ) -> ContextEntity:
        """Create a context entity in the backend."""
        return self.crud_processor.create_context_entity(_entity=_entity, **kwargs)

    def log_material_entity(
        self,
        **kwargs,
    ) -> MaterialEntity:
        """Create a material entity in the backend and upload associated files."""
        return self.material_processor.log_material_entity(self.crud_processor, **kwargs)

    def read_context_entity(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> ContextEntity:
        """Read a context entity from the backend."""
        return self.crud_processor.read_context_entity(
            identifier=identifier,
            entity_type=entity_type,
            project=project,
            entity_id=entity_id,
            **kwargs,
        )

    def read_unversioned_entity(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> UnversionedEntity:
        """Read an unversioned entity from the backend."""
        return self.crud_processor.read_unversioned_entity(
            identifier=identifier,
            entity_type=entity_type,
            project=project,
            entity_id=entity_id,
            **kwargs,
        )

    def read_context_entity_versions(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        **kwargs,
    ) -> list[ContextEntity]:
        """Read all versions of a context entity from the backend."""
        return self.crud_processor.read_context_entity_versions(
            identifier=identifier,
            entity_type=entity_type,
            project=project,
            **kwargs,
        )

    def list_context_entities(
        self,
        project: str,
        entity_type: str,
        **kwargs,
    ) -> list[ContextEntity]:
        """List all latest version context entities from the backend."""
        return self.crud_processor.list_context_entities(
            project=project,
            entity_type=entity_type,
            **kwargs,
        )

    def update_context_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        entity_dict: dict,
        **kwargs,
    ) -> ContextEntity:
        """Update a context entity in the backend."""
        return self.crud_processor.update_context_entity(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_dict=entity_dict,
            **kwargs,
        )

    def delete_context_entity(
        self,
        identifier: str,
        project: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        """Delete a context entity from the backend."""
        return self.crud_processor.delete_context_entity(
            identifier=identifier,
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs,
        )

    ##############################
    # Import/Export operations
    ##############################

    def import_context_entity(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> ContextEntity:
        """Import a context entity from a YAML file or from a storage key."""
        return self.import_export_processor.import_context_entity(
            crud_processor=self.crud_processor,
            file=file,
            key=key,
            reset_id=reset_id,
            context=context,
        )

    def import_executable_entity(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> ExecutableEntity:
        """Import an executable entity from a YAML file or from a storage key."""
        return self.import_export_processor.import_executable_entity(
            crud_processor=self.crud_processor,
            file=file,
            key=key,
            reset_id=reset_id,
            context=context,
        )

    def load_context_entity(
        self,
        file: str,
    ) -> ContextEntity:
        """Load a context entity from a YAML file and update it in the backend."""
        return self.import_export_processor.load_context_entity(
            crud_processor=self.crud_processor,
            file=file,
        )

    def load_executable_entity(
        self,
        file: str,
    ) -> ExecutableEntity:
        """Load an executable entity from a YAML file and update it in the backend."""
        return self.import_export_processor.load_executable_entity(
            crud_processor=self.crud_processor,
            file=file,
        )

    ##############################
    # Context entity operations
    ##############################

    def build_context_entity_key(
        self,
        project: str,
        entity_type: str,
        entity_kind: str,
        entity_name: str,
        entity_id: str | None = None,
    ) -> str:
        """Build a storage key for a context entity."""
        return self.special_ops_processor.build_context_entity_key(
            project=project,
            entity_type=entity_type,
            entity_kind=entity_kind,
            entity_name=entity_name,
            entity_id=entity_id,
        )

    def read_secret_data(
        self,
        project: str,
        entity_type: str,
        **kwargs,
    ) -> dict:
        """Read secret data from the backend."""
        return self.special_ops_processor.read_secret_data(
            project=project,
            entity_type=entity_type,
            **kwargs,
        )

    def update_secret_data(
        self,
        project: str,
        entity_type: str,
        data: dict,
        **kwargs,
    ) -> None:
        """Update secret data in the backend."""
        return self.special_ops_processor.update_secret_data(
            project=project,
            entity_type=entity_type,
            data=data,
            **kwargs,
        )

    def read_run_logs(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> dict:
        """Read execution logs from the backend."""
        return self.special_ops_processor.read_run_logs(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs,
        )

    def stop_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> None:
        """Stop a running entity in the backend."""
        return self.special_ops_processor.stop_entity(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs,
        )

    def resume_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> None:
        """Resume a stopped entity in the backend."""
        return self.special_ops_processor.resume_entity(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs,
        )

    def read_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> list[dict]:
        """Read file information from the backend."""
        return self.special_ops_processor.read_files_info(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs,
        )

    def update_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        entity_list: list[dict],
        **kwargs,
    ) -> None:
        """Get files info from backend."""
        return self.special_ops_processor.update_files_info(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_list=entity_list,
            **kwargs,
        )

    def read_metrics(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str | None = None,
        **kwargs,
    ) -> dict:
        """Read metrics from the backend for a specific entity."""
        return self.special_ops_processor.read_metrics(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            **kwargs,
        )

    def update_metric(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        metric_value: Any,
        **kwargs,
    ) -> None:
        """Update or create a metric value for an entity in the backend."""
        return self.special_ops_processor.update_metric(
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            metric_value=metric_value,
            **kwargs,
        )

    def search_entity(
        self,
        project: str,
        query: str | None = None,
        entity_types: list[str] | None = None,
        name: str | None = None,
        kind: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> list[ContextEntity]:
        """Search for entities in the backend using various criteria."""
        return self.special_ops_processor.search_entity(
            crud_processor=self.crud_processor,
            project=project,
            query=query,
            entity_types=entity_types,
            name=name,
            kind=kind,
            created=created,
            updated=updated,
            description=description,
            labels=labels,
            **kwargs,
        )
