# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.utils import get_context_from_identifier, get_context_from_project
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.executable.entity import ExecutableEntity
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor


class ContextEntityImportExportProcessor:
    """
    Processor for import and export operations on context entities.

    Handles loading entities from YAML files and importing/exporting
    entity configurations between local files and the backend.
    """

    def import_context_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> ContextEntity:
        """
        Import a context entity from a YAML file or from a storage key.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        file : str
            Path to the YAML file containing entity configuration.
        key : str
            Storage key (store://...) to read the entity from.
        reset_id : bool
            Flag to determine if the ID of context entities should be reset.
        context : str
            Project name to use for context resolution. If None, uses
            the project specified in the YAML file.

        Returns
        -------
        ContextEntity
            The imported and created context entity.

        Raises
        ------
        EntityError
            If the entity already exists in the backend.
        """
        if (file is None) == (key is None):
            raise ValueError("Provide key or file, not both or none.")

        if file is not None:
            dict_obj: dict = read_yaml(file)
        else:
            ctx = get_context_from_identifier(key)
            dict_obj: dict = crud_processor._read_context_entity(ctx, key)

        dict_obj["status"] = {}

        if context is None:
            context = dict_obj["project"]

        ctx = get_context_from_project(context)
        obj = entity_factory.build_entity_from_dict(dict_obj)
        if reset_id:
            new_id = build_uuid()
            obj.id = new_id
            obj.metadata.version = new_id
        try:
            bck_obj = crud_processor._create_context_entity(ctx, obj.ENTITY_TYPE, obj.to_dict())
            new_obj: ContextEntity = entity_factory.build_entity_from_dict(bck_obj)
        except EntityAlreadyExistsError:
            raise EntityError(f"Entity {obj.name} already exists. If you want to update it, use load instead.")
        return new_obj

    def import_executable_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> ExecutableEntity:
        """
        Import an executable entity from a YAML file or from a storage key.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        file : str
            Path to the YAML file containing executable entity configuration.
            Can contain a single entity or a list with the executable and tasks.
        key : str
            Storage key (store://...) to read the entity from.
        reset_id : bool
            Flag to determine if the ID of executable entities should be reset.
        context : str
            Project name to use for context resolution.

        Returns
        -------
        ExecutableEntity
            The imported and created executable entity.

        Raises
        ------
        EntityError
            If the entity already exists in the backend.
        """
        if (file is None) == (key is None):
            raise ValueError("Provide key or file, not both or none.")

        if file is not None:
            dict_obj: dict | list[dict] = read_yaml(file)
        else:
            ctx = get_context_from_identifier(key)
            dict_obj: dict = crud_processor._read_context_entity(ctx, key)

        if isinstance(dict_obj, list):
            exec_dict = dict_obj[0]
            exec_dict["status"] = {}
            tsk_dicts = []
            for i in dict_obj[1:]:
                i["status"] = {}
                tsk_dicts.append(i)
        else:
            exec_dict = dict_obj
            exec_dict["status"] = {}
            tsk_dicts = []

        if context is None:
            context = exec_dict["project"]

        ctx = get_context_from_project(context)
        obj: ExecutableEntity = entity_factory.build_entity_from_dict(exec_dict)

        if reset_id:
            new_id = build_uuid()
            obj.id = new_id
            obj.metadata.version = new_id

        try:
            bck_obj = crud_processor._create_context_entity(ctx, obj.ENTITY_TYPE, obj.to_dict())
            new_obj: ExecutableEntity = entity_factory.build_entity_from_dict(bck_obj)
        except EntityAlreadyExistsError:
            raise EntityError(f"Entity {obj.name} already exists. If you want to update it, use load instead.")

        new_obj.import_tasks(tsk_dicts)

        return new_obj

    def load_context_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        file: str,
    ) -> ContextEntity:
        """
        Load a context entity from a YAML file and update it in the backend.

        Reads entity configuration from a YAML file and updates an existing
        entity in the backend. If the entity doesn't exist, it creates a
        new one.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        file : str
            Path to the YAML file containing entity configuration.

        Returns
        -------
        ContextEntity
            The loaded and updated context entity.
        """
        dict_obj: dict = read_yaml(file)
        context = get_context_from_project(dict_obj["project"])
        obj: ContextEntity = entity_factory.build_entity_from_dict(dict_obj)
        try:
            crud_processor._update_context_entity(context, obj.ENTITY_TYPE, obj.id, obj.to_dict())
        except EntityNotExistsError:
            crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        return obj

    def load_executable_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        file: str,
    ) -> ExecutableEntity:
        """
        Load an executable entity from a YAML file and update it in the backend.

        Reads executable entity configuration from a YAML file and updates
        an existing executable entity in the backend. If the entity doesn't
        exist, it creates a new one. Also handles task imports.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        file : str
            Path to the YAML file containing executable entity configuration.
            Can contain a single entity or a list with the executable and tasks.

        Returns
        -------
        ExecutableEntity
            The loaded and updated executable entity.
        """
        dict_obj: dict | list[dict] = read_yaml(file)
        if isinstance(dict_obj, list):
            exec_dict = dict_obj[0]
            tsk_dicts = dict_obj[1:]
        else:
            exec_dict = dict_obj
            tsk_dicts = []

        context = get_context_from_project(exec_dict["project"])
        obj: ExecutableEntity = entity_factory.build_entity_from_dict(exec_dict)

        try:
            crud_processor._update_context_entity(context, obj.ENTITY_TYPE, obj.id, obj.to_dict())
        except EntityNotExistsError:
            crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        obj.import_tasks(tsk_dicts)
        return obj
