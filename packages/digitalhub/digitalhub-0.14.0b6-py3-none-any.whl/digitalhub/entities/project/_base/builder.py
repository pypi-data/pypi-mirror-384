# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.builder import EntityBuilder
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.project._base.spec import ProjectSpec, ProjectValidator
from digitalhub.entities.project._base.status import ProjectStatus


class ProjectProjectBuilder(EntityBuilder):
    """
    ProjectProject builder.
    """

    ENTITY_TYPE = EntityTypes.PROJECT.value
    ENTITY_CLASS = Project
    ENTITY_SPEC_CLASS = ProjectSpec
    ENTITY_SPEC_VALIDATOR = ProjectValidator
    ENTITY_STATUS_CLASS = ProjectStatus
    ENTITY_KIND = EntityKinds.PROJECT_PROJECT.value

    def build(
        self,
        name: str,
        kind: str,
        description: str | None = None,
        labels: list[str] | None = None,
        local: bool = False,
        config: dict | None = None,
        context: str | None = None,
        **kwargs,
    ) -> Project:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        local : bool
            If True, use local backend, if False use DHCore backend. Default to False.
        config : dict
            DHCore environment configuration.
        context : str
            The context local folder of the project.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Project
            Object instance.
        """
        name = self.build_name(name)
        metadata = self.build_metadata(
            project=name,
            name=name,
            description=description,
            labels=labels,
        )
        spec = self.build_spec(
            config=config,
            context=context,
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            name=name,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
            local=local,
        )

    def from_dict(self, obj: dict, validate: bool = True) -> Project:
        """
        Create a new object from dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary to create object from.
        validate : bool
            Flag to indicate if arguments must be validated.

        Returns
        -------
        Project
            Object instance.
        """
        parsed_dict = self._parse_dict(obj, validate=validate)
        return self.build_entity(**parsed_dict)

    def _parse_dict(self, obj: dict, validate: bool = True) -> dict:
        """
        Get dictionary and parse it to a valid entity dictionary.

        Parameters
        ----------
        entity : str
            Entity type.
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        name = self.build_name(obj.get("name"))
        kind = obj.get("kind")
        local = obj.get("local", False)
        metadata = self.build_metadata(**obj.get("metadata", {}))
        spec = self.build_spec(validate=validate, **obj.get("spec", {}))
        status = self.build_status(**obj.get("status", {}))
        user = obj.get("user")
        return {
            "name": name,
            "kind": kind,
            "metadata": metadata,
            "spec": spec,
            "status": status,
            "user": user,
            "local": local,
        }
