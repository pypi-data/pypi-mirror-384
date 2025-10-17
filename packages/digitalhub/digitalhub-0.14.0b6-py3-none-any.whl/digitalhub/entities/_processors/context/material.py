# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import Relationship, State
from digitalhub.entities._processors.utils import get_context_from_project
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.material.entity import MaterialEntity
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor


class ContextEntityMaterialProcessor:
    """
    Processor for material entity operations.

    Handles creation and management of material entities (artifacts,
    dataitems, models) including file upload operations and status
    management during uploads.
    """

    def log_material_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        **kwargs,
    ) -> MaterialEntity:
        """
        Create a material entity in the backend and upload associated files.

        Creates a new material entity (artifact, dataitem, or model) and
        handles file upload operations. Manages upload state transitions
        and error handling during the upload process.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        **kwargs : dict
            Parameters for entity creation including:
            - 'source': file source(s) to upload
            - 'project': project name
            - other entity-specific parameters

        Returns
        -------
        MaterialEntity
            The created material entity with uploaded files.

        Raises
        ------
        EntityError
            If file upload fails during the process.
        """
        source: SourcesOrListOfSources = kwargs.pop("source")
        context = get_context_from_project(kwargs["project"])
        obj = entity_factory.build_entity_from_params(**kwargs)
        if context.is_running:
            obj.add_relationship(Relationship.PRODUCEDBY.value, context.get_run_ctx())

        new_obj: MaterialEntity = crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        new_obj = entity_factory.build_entity_from_dict(new_obj)

        new_obj.status.state = State.UPLOADING.value
        new_obj = self._update_material_entity(crud_processor, new_obj)

        # Handle file upload
        try:
            new_obj.upload(source)
            uploaded = True
            msg = None
        except Exception as e:
            uploaded = False
            msg = str(e.args)

        new_obj.status.message = msg

        # Update status after upload
        if uploaded:
            new_obj.status.state = State.READY.value
            new_obj = self._update_material_entity(crud_processor, new_obj)
        else:
            new_obj.status.state = State.ERROR.value
            new_obj = self._update_material_entity(crud_processor, new_obj)
            raise EntityError(msg)

        return new_obj

    def _update_material_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        new_obj: MaterialEntity,
    ) -> MaterialEntity:
        """
        Update a material entity using a shortcut method.

        Convenience method for updating material entities during
        file upload operations.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        new_obj : MaterialEntity
            The material entity object to update.

        Returns
        -------
        MaterialEntity
            The updated material entity.
        """
        return crud_processor.update_context_entity(
            new_obj.project,
            new_obj.ENTITY_TYPE,
            new_obj.id,
            new_obj.to_dict(),
        )
