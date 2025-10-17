# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import Any

from digitalhub.context.api import build_context
from digitalhub.entities._base.entity.entity import Entity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.processors import base_processor, context_processor
from digitalhub.entities.artifact.crud import (
    delete_artifact,
    get_artifact,
    get_artifact_versions,
    import_artifact,
    list_artifacts,
    log_artifact,
    new_artifact,
    update_artifact,
)
from digitalhub.entities.dataitem.crud import (
    delete_dataitem,
    get_dataitem,
    get_dataitem_versions,
    import_dataitem,
    list_dataitems,
    log_dataitem,
    new_dataitem,
    update_dataitem,
)
from digitalhub.entities.function.crud import (
    delete_function,
    get_function,
    get_function_versions,
    import_function,
    list_functions,
    new_function,
    update_function,
)
from digitalhub.entities.model.crud import (
    delete_model,
    get_model,
    get_model_versions,
    import_model,
    list_models,
    log_model,
    new_model,
    update_model,
)
from digitalhub.entities.run.crud import delete_run, get_run, list_runs
from digitalhub.entities.secret.crud import (
    delete_secret,
    get_secret,
    get_secret_versions,
    import_secret,
    list_secrets,
    new_secret,
    update_secret,
)
from digitalhub.entities.workflow.crud import (
    delete_workflow,
    get_workflow,
    get_workflow_versions,
    import_workflow,
    list_workflows,
    new_workflow,
    update_workflow,
)
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.api import get_client
from digitalhub.utils.exceptions import BackendError, EntityAlreadyExistsError, EntityError
from digitalhub.utils.generic_utils import get_timestamp
from digitalhub.utils.io_utils import write_yaml
from digitalhub.utils.uri_utils import has_local_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.artifact._base.entity import Artifact
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.entities.function._base.entity import Function
    from digitalhub.entities.model._base.entity import Model
    from digitalhub.entities.project._base.spec import ProjectSpec
    from digitalhub.entities.project._base.status import ProjectStatus
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.secret._base.entity import Secret
    from digitalhub.entities.workflow._base.entity import Workflow


class Project(Entity):
    """
    A class representing a project.
    """

    ENTITY_TYPE = EntityTypes.PROJECT.value

    def __init__(
        self,
        name: str,
        kind: str,
        metadata: Metadata,
        spec: ProjectSpec,
        status: ProjectStatus,
        user: str | None = None,
        local: bool = False,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)
        self.spec: ProjectSpec
        self.status: ProjectStatus

        self.id = name
        self.name = name
        self.key = base_processor.build_project_key(self.name, local=local)

        self._obj_attr.extend(["id", "name"])

        # Set client
        self._client = get_client(local)

        # Set context
        build_context(self)

    ##############################
    #  Save / Refresh / Export
    ##############################

    def save(self, update: bool = False) -> Project:
        """
        Save entity into backend.

        Parameters
        ----------
        update : bool
            If True, the object will be updated.

        Returns
        -------
        Project
            Entity saved.
        """
        if update:
            if self._client.is_local():
                self.metadata.updated = get_timestamp()
            new_obj = base_processor.update_project_entity(
                entity_type=self.ENTITY_TYPE,
                entity_name=self.name,
                entity_dict=self.to_dict(),
                local=self._client.is_local(),
            )
        else:
            new_obj = base_processor.create_project_entity(_entity=self)
        self._update_attributes(new_obj)
        return self

    def refresh(self) -> Project:
        """
        Refresh object from backend.

        Returns
        -------
        Project
            Project object.
        """
        new_obj = base_processor.read_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
            local=self._client.is_local(),
        )
        self._update_attributes(new_obj)
        return self

    def search_entity(
        self,
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
        """
        Search objects from backend.

        Parameters
        ----------
        query : str
            Search query.
        entity_types : list[str]
            Entity types.
        name : str
            Entity name.
        kind : str
            Entity kind.
        created : str
            Entity creation date.
        updated : str
            Entity update date.
        description : str
            Entity description.
        labels : list[str]
            Entity labels.
        **kwargs : dict
            Parameters to pass to the API call.

            Returns
            -------
            list[ContextEntity]
                List of object instances.
        """
        objs = context_processor.search_entity(
            self.name,
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
        self.refresh()
        return objs

    def export(self) -> str:
        """
        Export object as a YAML file in the context folder.
        If the objects are not embedded, the objects are exported as a YAML file.

        Returns
        -------
        str
            Exported filepath.
        """
        obj = self._refresh_to_dict()
        pth = Path(self.spec.context) / f"{self.ENTITY_TYPE}s-{self.name}.yaml"
        obj = self._export_not_embedded(obj)
        write_yaml(pth, obj)
        return str(pth)

    def _refresh_to_dict(self) -> dict:
        """
        Try to refresh object to collect entities related to project.

        Returns
        -------
        dict
            Entity object in dictionary format.
        """
        try:
            return self.refresh().to_dict()
        except BackendError:
            return self.to_dict()

    def _export_not_embedded(self, obj: dict) -> dict:
        """
        Export project objects if not embedded.

        Parameters
        ----------
        obj : dict
            Project object in dictionary format.

        Returns
        -------
        dict
            Updatated project object in dictionary format with referenced entities.
        """
        # Cycle over entity types
        for entity_type in self._get_entity_types():
            # Entity types are stored as a list of entities
            for idx, entity in enumerate(obj.get("spec", {}).get(entity_type, [])):
                # Export entity if not embedded is in metadata, else do nothing
                if not self._is_embedded(entity):
                    # Get entity object from backend
                    ent = context_processor.read_context_entity(entity["key"])

                    # Export and store ref in object metadata inside project
                    pth = ent.export()
                    obj["spec"][entity_type][idx]["metadata"]["ref"] = pth

        # Return updated object
        return obj

    def _import_entities(self, obj: dict, reset_id: bool = False) -> None:
        """
        Import project entities.

        Parameters
        ----------
        obj : dict
            Project object in dictionary format.
        """
        entity_types = self._get_entity_types()

        # Cycle over entity types
        for entity_type in entity_types:
            # Entity types are stored as a list of entities
            for entity in obj.get("spec", {}).get(entity_type, []):
                embedded = self._is_embedded(entity)
                ref = entity["metadata"].get("ref")

                # Import entity if not embedded and there is a ref
                if not embedded and ref is not None:
                    # Import entity from local ref
                    if has_local_scheme(ref):
                        try:
                            # Artifacts, Dataitems and Models
                            if entity_type in entity_types[:3]:
                                context_processor.import_context_entity(
                                    file=ref,
                                    reset_id=reset_id,
                                    context=self.name,
                                )

                            # Functions and Workflows
                            elif entity_type in entity_types[3:]:
                                context_processor.import_executable_entity(
                                    file=ref,
                                    reset_id=reset_id,
                                    context=self.name,
                                )

                        except FileNotFoundError:
                            msg = f"File not found: {ref}."
                            raise EntityError(msg)

                # If entity is embedded, create it and try to save
                elif embedded:
                    # It's possible that embedded field in metadata is not shown
                    if entity["metadata"].get("embedded") is None:
                        entity["metadata"]["embedded"] = True

                    if reset_id:
                        new_id = build_uuid()
                        entity["id"] = new_id
                        entity["metadata"]["version"] = new_id

                    try:
                        entity_factory.build_entity_from_dict(entity).save()
                    except EntityAlreadyExistsError:
                        pass

    def _load_entities(self, obj: dict) -> None:
        """
        Load project entities.

        Parameters
        ----------
        obj : dict
            Project object in dictionary format.
        """
        entity_types = self._get_entity_types()

        # Cycle over entity types
        for entity_type in entity_types:
            # Entity types are stored as a list of entities
            for entity in obj.get("spec", {}).get(entity_type, []):
                embedded = self._is_embedded(entity)
                ref = entity["metadata"].get("ref")

                # Load entity if not embedded and there is a ref
                if not embedded and ref is not None:
                    # Load entity from local ref
                    if has_local_scheme(ref):
                        try:
                            # Artifacts, Dataitems and Models
                            if entity_type in entity_types[:3]:
                                context_processor.load_context_entity(ref)

                            # Functions and Workflows
                            elif entity_type in entity_types[3:]:
                                context_processor.load_executable_entity(ref)

                        except FileNotFoundError:
                            msg = f"File not found: {ref}."
                            raise EntityError(msg)

    def _is_embedded(self, entity: dict) -> bool:
        """
        Check if entity is embedded.

        Parameters
        ----------
        entity : dict
            Entity in dictionary format.

        Returns
        -------
        bool
            True if entity is embedded.
        """
        metadata_embedded = entity["metadata"].get("embedded", False)
        no_status = entity.get("status", None) is None
        no_spec = entity.get("spec", None) is None
        return metadata_embedded or not (no_status and no_spec)

    def _get_entity_types(self) -> list[str]:
        """
        Get entity types.

        Returns
        -------
        list
            Entity types.
        """
        return [
            f"{EntityTypes.ARTIFACT.value}s",
            f"{EntityTypes.DATAITEM.value}s",
            f"{EntityTypes.MODEL.value}s",
            f"{EntityTypes.FUNCTION.value}s",
            f"{EntityTypes.WORKFLOW.value}s",
        ]

    ##############################
    #  Artifacts
    ##############################

    def new_artifact(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        path : str
            Object path on local file system or remote storage. It is also the destination path of upload() method.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        >>> obj = project.new_artifact(name="my-artifact",
        >>>                            kind="artifact",
        >>>                            path="s3://my-bucket/my-key")
        """
        obj = new_artifact(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def log_artifact(
        self,
        name: str,
        kind: str,
        source: str,
        path: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Create and upload an object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        source : str
            Artifact location on local path.
        path : str
            Destination path of the artifact. If not provided, it's generated.
        **kwargs : dict
            New artifact spec parameters.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        >>> obj = project.log_artifact(name="my-artifact",
        >>>                            kind="artifact",
        >>>                            source="./local-path")
        """
        obj = log_artifact(
            project=self.name,
            name=name,
            kind=kind,
            source=source,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_artifact(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Artifact:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_artifact("store://my-artifact-key")

        Using entity name:
        >>> obj = project.get_artifact("my-artifact-name"
        >>>                            entity_id="my-artifact-id")
        """
        obj = get_artifact(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
        )
        self.refresh()
        return obj

    def get_artifact_versions(
        self,
        identifier: str,
    ) -> list[Artifact]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.

        Returns
        -------
        list[Artifact]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_artifact_versions("store://my-artifact-key")

        Using entity name:
        >>> obj = project.get_artifact_versions("my-artifact-name")
        """
        return get_artifact_versions(identifier, project=self.name)

    def list_artifacts(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        version: str | None = None,
    ) -> list[Artifact]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        version : str
            Object version, default is latest.

        Returns
        -------
        list[Artifact]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_artifacts()
        """
        return list_artifacts(
            self.name,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            version=version,
        )

    def import_artifact(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Artifact:
        """
        Import object from a YAML file and create a new object into the backend.

        Parameters
        ----------
        file : str
            Path to YAML file.
        key : str
            Entity key (store://...).
        reset_id : bool
            Flag to determine if the ID of context entities should be reset.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        >>> obj = project.import_artifact("my-artifact.yaml")
        """
        return import_artifact(file, key, reset_id, self.name)

    def update_artifact(self, entity: Artifact) -> Artifact:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Artifact
            Object to update.

        Returns
        -------
        Artifact
            Entity updated.

        Examples
        --------
        >>> obj = project.update_artifact(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_artifact(entity)

    def delete_artifact(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_artifact("store://my-artifact-key")

        Otherwise:
        >>> project.delete_artifact("my-artifact-name",
        >>>                         delete_all_versions=True)
        """
        delete_artifact(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
        )
        self.refresh()

    ##############################
    #  Dataitems
    ##############################

    def new_dataitem(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        path : str
            Object path on local file system or remote storage. It is also the destination path of upload() method.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        >>> obj = project.new_dataitem(name="my-dataitem",
        >>>                            kind="dataitem",
        >>>                            path="s3://my-bucket/my-key")
        """
        obj = new_dataitem(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def log_dataitem(
        self,
        name: str,
        kind: str,
        source: str | None = None,
        data: Any | None = None,
        extension: str | None = None,
        path: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create and upload an object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        data : Any
            Dataframe to log.
        extension : str
            Extension of the dataitem.
        source : str
            Dataitem location on local path.
        data : Any
            Dataframe to log. Alternative to source.
        extension : str
            Extension of the output dataframe.
        path : str
            Destination path of the dataitem. If not provided, it's generated.
        **kwargs : dict
            New dataitem spec parameters.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        >>> obj = project.log_dataitem(name="my-dataitem",
        >>>                            kind="table",
        >>>                            data=df)
        """
        obj = log_dataitem(
            project=self.name,
            name=name,
            kind=kind,
            path=path,
            source=source,
            data=data,
            extension=extension,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_dataitem(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Dataitem:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_dataitem("store://my-dataitem-key")

        Using entity name:
        >>> obj = project.get_dataitem("my-dataitem-name"
        >>>                            entity_id="my-dataitem-id")
        """
        obj = get_dataitem(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
        )
        self.refresh()
        return obj

    def get_dataitem_versions(
        self,
        identifier: str,
    ) -> list[Dataitem]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.

        Returns
        -------
        list[Dataitem]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_dataitem_versions("store://my-dataitem-key")

        Using entity name:
        >>> obj = project.get_dataitem_versions("my-dataitem-name")
        """
        return get_dataitem_versions(identifier, project=self.name)

    def list_dataitems(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        version: str | None = None,
    ) -> list[Dataitem]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        version : str
            Object version, default is latest.

        Returns
        -------
        list[Dataitem]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_dataitems()
        """
        return list_dataitems(
            self.name,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            version=version,
        )

    def import_dataitem(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Dataitem:
        """
        Import object from a YAML file and create a new object into the backend.

        Parameters
        ----------
        file : str
            Path to YAML file.
        key : str
            Entity key (store://...).
        reset_id : bool
            Flag to determine if the ID of context entities should be reset.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        >>> obj = project.import_dataitem("my-dataitem.yaml")
        """
        return import_dataitem(file, key, reset_id, self.name)

    def update_dataitem(self, entity: Dataitem) -> Dataitem:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Dataitem
            Object to update.

        Returns
        -------
        Dataitem
            Entity updated.

        Examples
        --------
        >>> obj = project.update_dataitem(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_dataitem(entity)

    def delete_dataitem(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_dataitem("store://my-dataitem-key")

        Otherwise:
        >>> project.delete_dataitem("my-dataitem-name",
        >>>                         project="my-project",
        >>>                         delete_all_versions=True)
        """
        delete_dataitem(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
        )
        self.refresh()

    ##############################
    #  Models
    ##############################

    def new_model(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        path : str
            Object path on local file system or remote storage. It is also the destination path of upload() method.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        >>> obj = project.new_model(name="my-model",
        >>>                            kind="model",
        >>>                            path="s3://my-bucket/my-key")
        """
        obj = new_model(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def log_model(
        self,
        name: str,
        kind: str,
        source: str,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create and upload an object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        source : str
            Model location on local path.
        path : str
            Destination path of the model. If not provided, it's generated.
        **kwargs : dict
            New model spec parameters.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        >>> obj = project.log_model(name="my-model",
        >>>                            kind="model",
        >>>                            source="./local-path")
        """
        obj = log_model(
            project=self.name,
            name=name,
            kind=kind,
            source=source,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_model(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Model:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_model("store://my-model-key")

        Using entity name:
        >>> obj = project.get_model("my-model-name"
        >>>                            entity_id="my-model-id")
        """
        obj = get_model(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
        )
        self.refresh()
        return obj

    def get_model_versions(
        self,
        identifier: str,
    ) -> list[Model]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.

        Returns
        -------
        list[Model]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_model_versions("store://my-model-key")

        Using entity name:
        >>> obj = project.get_model_versions("my-model-name")
        """
        return get_model_versions(identifier, project=self.name)

    def list_models(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        version: str | None = None,
    ) -> list[Model]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        version : str
            Object version, default is latest.

        Returns
        -------
        list[Model]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_models()
        """
        return list_models(
            self.name,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            version=version,
        )

    def import_model(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Model:
        """
        Import object from a YAML file and create a new object into the backend.

        Parameters
        ----------
        file : str
            Path to YAML file.
        key : str
            Entity key (store://...).
        reset_id : bool
            Flag to determine if the ID of context entities should be reset.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        >>> obj = project.import_model("my-model.yaml")
        """
        return import_model(file, key, reset_id, self.name)

    def update_model(self, entity: Model) -> Model:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Model
            Object to update.

        Returns
        -------
        Model
            Entity updated.

        Examples
        --------
        >>> obj = project.update_model(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_model(entity)

    def delete_model(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_model("store://my-model-key")

        Otherwise:
        >>> project.delete_model("my-model-name",
        >>>                         project="my-project",
        >>>                         delete_all_versions=True)
        """
        delete_model(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
        )
        self.refresh()

    ##############################
    #  Functions
    ##############################

    def new_function(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        **kwargs,
    ) -> Function:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Function
            Object instance.

        Examples
        --------
        >>> obj = project.new_function(name="my-function",
        >>>                            kind="python",
        >>>                            code_src="function.py",
        >>>                            handler="function-handler")
        """
        obj = new_function(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_function(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Function:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.

        Returns
        -------
        Function
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_function("store://my-function-key")

        Using entity name:
        >>> obj = project.get_function("my-function-name"
        >>>                            entity_id="my-function-id")
        """
        obj = get_function(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
        )
        self.refresh()
        return obj

    def get_function_versions(
        self,
        identifier: str,
    ) -> list[Function]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.

        Returns
        -------
        list[Function]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_function_versions("store://my-function-key")

        Using entity name:
        >>> obj = project.get_function_versions("my-function-name")
        """
        return get_function_versions(identifier, project=self.name)

    def list_functions(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        version: str | None = None,
    ) -> list[Function]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        version : str
            Object version, default is latest.

        Returns
        -------
        list[Function]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_functions()
        """
        return list_functions(
            self.name,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            version=version,
        )

    def import_function(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Function:
        """
        Import object from a YAML file and create a new object into the backend.

        Parameters
        ----------
        file : str
            Path to YAML file.
        key : str
            Entity key (store://...).
        reset_id : bool
            Flag to determine if the ID of context entities should be reset.

        Returns
        -------
        Function
            Object instance.

        Examples
        --------
        >>> obj = project.import_function("my-function.yaml")
        """
        return import_function(file, key, reset_id, self.name)

    def update_function(self, entity: Function) -> Function:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Function
            Object to update.

        Returns
        -------
        Function
            Entity updated.

        Examples
        --------
        >>> obj = project.update_function(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_function(entity)

    def delete_function(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        cascade : bool
            Cascade delete.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_function("store://my-function-key")

        Otherwise:
        >>> project.delete_function("my-function-name",
        >>>                         delete_all_versions=True)
        """
        delete_function(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
        )
        self.refresh()

    ##############################
    #  Workflows
    ##############################

    def new_workflow(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        **kwargs,
    ) -> Workflow:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Workflow
            Object instance.

        Examples
        --------
        >>> obj = project.new_workflow(name="my-workflow",
        >>>                            kind="kfp",
        >>>                            code_src="pipeline.py",
        >>>                            handler="pipeline-handler")
        """
        obj = new_workflow(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_workflow(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Workflow:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.

        Returns
        -------
        Workflow
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_workflow("store://my-workflow-key")

        Using entity name:
        >>> obj = project.get_workflow("my-workflow-name"
        >>>                            entity_id="my-workflow-id")
        """
        obj = get_workflow(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
        )
        self.refresh()
        return obj

    def get_workflow_versions(
        self,
        identifier: str,
    ) -> list[Workflow]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.

        Returns
        -------
        list[Workflow]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_workflow_versions("store://my-workflow-key")

        Using entity name:
        >>> obj = project.get_workflow_versions("my-workflow-name")
        """
        return get_workflow_versions(identifier, project=self.name)

    def list_workflows(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        version: str | None = None,
    ) -> list[Workflow]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        version : str
            Object version, default is latest.

        Returns
        -------
        list[Workflow]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_workflows()
        """
        return list_workflows(
            self.name,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            version=version,
        )

    def import_workflow(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Workflow:
        """
        Import object from a YAML file and create a new object into the backend.

        Parameters
        ----------
        file : str
            Path to YAML file.
        key : str
            Entity key (store://...).
        reset_id : bool
            Flag to determine if the ID of context entities should be reset.

        Returns
        -------
        Workflow
            Object instance.

        Examples
        --------
        >>> obj = project.import_workflow("my-workflow.yaml")
        """
        return import_workflow(file, key, reset_id, self.name)

    def update_workflow(self, entity: Workflow) -> Workflow:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Workflow
            Object to update.

        Returns
        -------
        Workflow
            Entity updated.

        Examples
        --------
        >>> obj = project.update_workflow(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_workflow(entity)

    def delete_workflow(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        cascade : bool
            Cascade delete.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_workflow("store://my-workflow-key")

        Otherwise:
        >>> project.delete_workflow("my-workflow-name",
        >>>                         delete_all_versions=True)
        """
        delete_workflow(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
        )
        self.refresh()

    ##############################
    #  Secrets
    ##############################

    def new_secret(
        self,
        name: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        secret_value: str | None = None,
        **kwargs,
    ) -> Secret:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        secret_value : str
            Value of the secret.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Secret
            Object instance.

        Examples
        --------
        >>> obj = project.new_secret(name="my-secret",
        >>>                          secret_value="my-secret-value")
        """
        obj = new_secret(
            project=self.name,
            name=name,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            secret_value=secret_value,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_secret(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Secret:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.

        Returns
        -------
        Secret
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_secret("store://my-secret-key")

        Using entity name:
        >>> obj = project.get_secret("my-secret-name"
        >>>                          entity_id="my-secret-id")
        """
        obj = get_secret(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
        )
        self.refresh()
        return obj

    def get_secret_versions(
        self,
        identifier: str,
    ) -> list[Secret]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.

        Returns
        -------
        list[Secret]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_secret_versions("store://my-secret-key")

        Using entity name:
        >>> obj = project.get_secret_versions("my-secret-name")
        """
        return get_secret_versions(identifier, project=self.name)

    def list_secrets(self) -> list[Secret]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Secret]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_secrets()
        """
        return list_secrets(self.name)

    def import_secret(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Secret:
        """
        Import object from a YAML file and create a new object into the backend.

        Parameters
        ----------
        file : str
            Path to YAML file.
        key : str
            Entity key (store://...).
        reset_id : bool
            Flag to determine if the ID of context entities should be reset.

        Returns
        -------
        Secret
            Object instance.

        Examples
        --------
        >>> obj = project.import_secret("my-secret.yaml")
        """
        return import_secret(file, key, reset_id, self.name)

    def update_secret(self, entity: Secret) -> Secret:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Secret
            Object to update.

        Returns
        -------
        Secret
            Entity updated.

        Examples
        --------
        >>> obj = project.update_secret(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_secret(entity)

    def delete_secret(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_secret("store://my-secret-key")

        Otherwise:
        >>> project.delete_secret("my-secret-name",
        >>>                       delete_all_versions=True)
        """
        delete_secret(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
        )
        self.refresh()

    ##############################
    #  Runs
    ##############################

    def get_run(
        self,
        identifier: str,
    ) -> Run:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity ID.

        Returns
        -------
        Run
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_run("store://my-secret-key")

        Using entity ID:
        >>> obj = project.get_run("123")
        """
        obj = get_run(
            identifier=identifier,
            project=self.name,
        )
        self.refresh()
        return obj

    def list_runs(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        function: str | None = None,
        workflow: str | None = None,
        task: str | None = None,
        action: str | None = None,
    ) -> list[Run]:
        """
        List all latest objects from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        function : str
            Function key filter.
        workflow : str
            Workflow key filter.
        task : str
            Task string filter.
        action : str
            Action name filter.

        Returns
        -------
        list[Run]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_runs()
        """
        return list_runs(
            self.name,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            function=function,
            workflow=workflow,
            task=task,
            action=action,
        )

    def delete_run(
        self,
        identifier: str,
        entity_id: str,
    ) -> None:
        """
        Delete run from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        >>> project.delete_run("store://my-run-key")

        """
        delete_run(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
        )
        self.refresh()

    ##############################
    #  Project methods
    ##############################

    def run(self, workflow: str | None = None, **kwargs) -> Run:
        """
        Run workflow project.

        Parameters
        ----------
        workflow : str
            Workflow name.
        **kwargs : dict
            Keyword arguments passed to workflow.run().

        Returns
        -------
        Run
            Run instance.
        """
        self.refresh()

        workflow = workflow if workflow is not None else "main"

        for i in self.spec.workflows:
            if workflow in [i["name"], i["key"]]:
                entity = self.get_workflow(i["key"])
                break
        else:
            msg = f"Workflow {workflow} not found."
            raise EntityError(msg)

        return entity.run(**kwargs)

    def share(self, user: str) -> None:
        """
        Share project.

        Parameters
        ----------
        user : str
            User to share project with.
        Returns
        -------
        None
        """
        return base_processor.share_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
            user=user,
            unshare=False,
            local=self._client.is_local(),
        )

    def unshare(self, user: str) -> None:
        """
        Unshare project.

        Parameters
        ----------
        user : str
            User to unshare project with.
        Returns
        -------
        None
        """
        return base_processor.share_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
            user=user,
            unshare=True,
            local=self._client.is_local(),
        )
