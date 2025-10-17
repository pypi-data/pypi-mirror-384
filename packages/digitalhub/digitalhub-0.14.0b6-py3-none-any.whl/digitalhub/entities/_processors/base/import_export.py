# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.api import get_client
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub.entities._processors.base.crud import BaseEntityCRUDProcessor
    from digitalhub.entities.project._base.entity import Project


class BaseEntityImportExportProcessor:
    """
    Processor for import and export operations on base entities.

    Handles loading entities from YAML files and importing/exporting
    entity configurations between local files and the backend.
    """

    def import_project_entity(
        self,
        crud_processor: BaseEntityCRUDProcessor,
        file: str,
        **kwargs,
    ) -> Project:
        """
        Import a project entity from a YAML file and create it in the backend.

        Reads project configuration from a YAML file, creates a new project
        entity in the backend, and imports any related entities defined
        in the file. Raises an error if the project already exists.

        Parameters
        ----------
        crud_processor : BaseEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        file : str
            Path to the YAML file containing project configuration.
        **kwargs : dict
            Additional parameters including 'local' and 'reset_id' flags.

        Returns
        -------
        Project
            The imported and created project entity.

        Raises
        ------
        EntityError
            If the project already exists in the backend.
        """
        client = get_client(kwargs.pop("local", False))
        obj: dict = read_yaml(file)
        obj["status"] = {}
        obj["local"] = client.is_local()
        ent: Project = entity_factory.build_entity_from_dict(obj)
        reset_id = kwargs.pop("reset_id", False)

        try:
            crud_processor._create_base_entity(ent._client, ent.ENTITY_TYPE, ent.to_dict())
        except EntityAlreadyExistsError:
            msg = f"Entity {ent.name} already exists."
            if reset_id:
                ent._import_entities(obj, reset_id=reset_id)
                warn(f"{msg} Other entities ids have been imported.")
                ent.refresh()
                return ent
            raise EntityError(f"{msg} If you want to update it, use load instead.")

        # Import related entities
        ent._import_entities(obj, reset_id=reset_id)
        ent.refresh()
        return ent

    def load_project_entity(
        self,
        crud_processor: BaseEntityCRUDProcessor,
        file: str,
        **kwargs,
    ) -> Project:
        """
        Load a project entity from a YAML file and update it in the backend.

        Reads project configuration from a YAML file and updates an existing
        project in the backend. If the project doesn't exist, it creates a
        new one. Also loads any related entities defined in the file.

        Parameters
        ----------
        crud_processor : BaseEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        file : str
            Path to the YAML file containing project configuration.
        **kwargs : dict
            Additional parameters including 'local' flag.

        Returns
        -------
        Project
            The loaded and updated project entity.
        """
        client = get_client(kwargs.pop("local", False))
        obj: dict = read_yaml(file)
        obj["local"] = client.is_local()
        ent: Project = entity_factory.build_entity_from_dict(obj)

        try:
            crud_processor._update_base_entity(ent._client, ent.ENTITY_TYPE, ent.name, ent.to_dict())
        except EntityNotExistsError:
            crud_processor._create_base_entity(ent._client, ent.ENTITY_TYPE, ent.to_dict())

        # Load related entities
        ent._load_entities(obj)
        ent.refresh()
        return ent
