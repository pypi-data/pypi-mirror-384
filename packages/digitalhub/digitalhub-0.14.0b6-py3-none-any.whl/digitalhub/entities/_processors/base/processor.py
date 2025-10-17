# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._processors.base.crud import BaseEntityCRUDProcessor
from digitalhub.entities._processors.base.import_export import BaseEntityImportExportProcessor
from digitalhub.entities._processors.base.special_ops import BaseEntitySpecialOpsProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project


class BaseEntityOperationsProcessor:
    """
    Processor for base entity operations.

    This class handles CRUD operations and other entity management tasks
    for base-level entities (primarily projects). It interacts with the
    client layer to perform backend operations and manages entity lifecycle
    including creation, reading, updating, deletion, and sharing.

    Uses composition with specialized processors for different operation types.
    """

    def __init__(self):
        self.crud_processor = BaseEntityCRUDProcessor()
        self.import_export_processor = BaseEntityImportExportProcessor()
        self.special_ops_processor = BaseEntitySpecialOpsProcessor()

    ##############################
    # CRUD base entity
    ##############################

    def create_project_entity(
        self,
        _entity: Project | None = None,
        **kwargs,
    ) -> Project:
        """
        Create a project entity in the backend.

        Creates a new project either from an existing entity object or
        by building one from the provided parameters. Handles both
        local and remote backend creation.

        Parameters
        ----------
        _entity : Project
            An existing project entity object to create. If None,
            a new entity will be built from kwargs.
        **kwargs : dict
            Parameters for entity creation, including 'local' flag
            and entity-specific parameters.

        Returns
        -------
        Project
            The created project entity with backend data populated.
        """
        return self.crud_processor.create_project_entity(_entity, **kwargs)

    def read_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        **kwargs,
    ) -> Project:
        """
        Read a project entity from the backend.

        Retrieves project data from the backend and constructs a
        Project entity object with the retrieved data.

        Parameters
        ----------
        entity_type : str
            The type of entity to read (typically 'project').
        entity_name : str
            The name identifier of the project to read.
        **kwargs : dict
            Additional parameters including 'local' flag and
            API call parameters.

        Returns
        -------
        Project
            The project entity object populated with backend data.
        """
        return self.crud_processor.read_project_entity(entity_type, entity_name, **kwargs)

    def update_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        entity_dict: dict,
        **kwargs,
    ) -> Project:
        """
        Update a project entity in the backend.

        Updates an existing project with new data and returns the
        updated Project entity object.

        Parameters
        ----------
        entity_type : str
            The type of entity to update (typically 'project').
        entity_name : str
            The name identifier of the project to update.
        entity_dict : dict
            The updated project data dictionary.
        **kwargs : dict
            Additional parameters including 'local' flag and
            API call parameters.

        Returns
        -------
        Project
            The updated project entity object.
        """
        return self.crud_processor.update_project_entity(entity_type, entity_name, entity_dict, **kwargs)

    def delete_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        **kwargs,
    ) -> dict:
        """
        Delete a project entity from the backend.

        Deletes a project from the backend and optionally cleans up
        the associated context. Handles both local and remote backends.

        Parameters
        ----------
        entity_type : str
            The type of entity to delete (typically 'project').
        entity_name : str
            The name identifier of the project to delete.
        **kwargs : dict
            Additional parameters including 'local' flag, 'clean_context'
            flag (default True), and API call parameters.

        Returns
        -------
        dict
            Response data from the backend delete operation.
        """
        return self.crud_processor.delete_project_entity(entity_type, entity_name, **kwargs)

    def list_project_entities(
        self,
        entity_type: str,
        **kwargs,
    ) -> list[Project]:
        """
        List project entities from the backend.

        Retrieves a list of projects from the backend and converts
        them to Project entity objects.

        Parameters
        ----------
        entity_type : str
            The type of entities to list (typically 'project').
        **kwargs : dict
            Additional parameters including 'local' flag and
            API call parameters for filtering or pagination.

        Returns
        -------
        list[Project]
            List of project entity objects.
        """
        return self.crud_processor.list_project_entities(entity_type, **kwargs)

    ##############################
    # Import/Export operations
    ##############################

    def import_project_entity(
        self,
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
        return self.import_export_processor.import_project_entity(self.crud_processor, file, **kwargs)

    def load_project_entity(
        self,
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
        file : str
            Path to the YAML file containing project configuration.
        **kwargs : dict
            Additional parameters including 'local' flag.

        Returns
        -------
        Project
            The loaded and updated project entity.
        """
        return self.import_export_processor.load_project_entity(self.crud_processor, file, **kwargs)

    ##############################
    # Base entity operations
    ##############################

    def build_project_key(
        self,
        entity_id: str,
        **kwargs,
    ) -> str:
        """
        Build a storage key for a project entity.

        Creates a standardized key string for project identification
        and storage, handling both local and remote client contexts.

        Parameters
        ----------
        entity_id : str
            The unique identifier of the project entity.
        **kwargs : dict
            Additional parameters including 'local' flag.

        Returns
        -------
        str
            The constructed project entity key string.
        """
        return self.special_ops_processor.build_project_key(entity_id, **kwargs)

    def share_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        **kwargs,
    ) -> None:
        """
        Share or unshare a project entity with a user.

        Manages project access permissions by sharing the project with
        a specified user or removing user access. Handles both sharing
        and unsharing operations based on the 'unshare' parameter.

        Parameters
        ----------
        entity_type : str
            The type of entity to share (typically 'project').
        entity_name : str
            The name identifier of the project to share.
        **kwargs : dict
            Additional parameters including:
            - 'user': username to share with/unshare from
            - 'unshare': boolean flag for unsharing (default False)
            - 'local': boolean flag for local backend

        Raises
        ------
        ValueError
            If trying to unshare from a user who doesn't have access.
        """
        return self.special_ops_processor.share_project_entity(entity_type, entity_name, **kwargs)
