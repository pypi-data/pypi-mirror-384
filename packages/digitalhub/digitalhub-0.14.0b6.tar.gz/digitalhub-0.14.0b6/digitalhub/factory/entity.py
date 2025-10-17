# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.factory.registry import registry
from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.entity import Entity
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities._base.entity.spec import Spec, SpecValidator
    from digitalhub.entities._base.entity.status import Status


class EntityFactory:
    """
    Factory for creating and managing entity builders.

    This class handles the creation of entities and their components
    through their respective builders, using a centralized registry.
    """

    def _call_builder_method(self, kind: str, method_name: str, *args, **kwargs):
        """
        Helper method to get a builder and call a method on it.

        Parameters
        ----------
        kind : str
            The kind of builder to retrieve.
        method_name : str
            The name of the method to call on the builder.
        *args
            Positional arguments to pass to the method.
        **kwargs
            Keyword arguments to pass to the method.

        Returns
        -------
        Any
            The result of calling the method on the builder.
        """
        builder = registry.get_entity_builder(kind)
        return getattr(builder, method_name)(*args, **kwargs)

    def build_entity_from_params(self, **kwargs) -> Entity:
        """
        Build an entity from parameters.

        Parameters
        ----------
        **kwargs
            Entity parameters.

        Returns
        -------
        Entity
            Entity object.
        """
        kind = self._get_kind(**kwargs)
        builder = registry.get_entity_builder(kind)
        return builder.build(**kwargs)

    def build_entity_from_dict(self, obj: dict) -> Entity:
        """
        Build an entity from a dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary with entity data.

        Returns
        -------
        Entity
            Entity object.
        """
        kind = self._get_kind(**obj)
        builder = registry.get_entity_builder(kind)
        return builder.from_dict(obj)

    def build_spec(self, kind_to_build_from: str, **kwargs) -> Spec:
        """
        Build an entity spec.

        Parameters
        ----------
        kind_to_build_from : str
            Entity type.
        **kwargs
            Additional spec parameters.

        Returns
        -------
        Spec
            Spec object.
        """
        return self._call_builder_method(kind_to_build_from, "build_spec", **kwargs)

    def build_metadata(self, kind_to_build_from: str, **kwargs) -> Metadata:
        """
        Build an entity metadata.

        Parameters
        ----------
        kind_to_build_from : str
            Entity type.
        **kwargs
            Additional metadata parameters.

        Returns
        -------
        Metadata
            Metadata object.
        """
        return self._call_builder_method(kind_to_build_from, "build_metadata", **kwargs)

    def build_status(self, kind_to_build_from: str, **kwargs) -> Status:
        """
        Build an entity status.

        Parameters
        ----------
        kind_to_build_from : str
            Entity type.
        **kwargs
            Additional status parameters.

        Returns
        -------
        Status
            Status object.
        """
        return self._call_builder_method(kind_to_build_from, "build_status", **kwargs)

    def get_entity_type_from_kind(self, kind: str) -> str:
        """
        Get entity type from builder.

        Parameters
        ----------
        kind : str
            Entity type.

        Returns
        -------
        str
            Entity type.
        """
        return self._call_builder_method(kind, "get_entity_type")

    def get_executable_kind(self, kind: str) -> str:
        """
        Get executable kind.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        str
            Executable kind.
        """
        return self._call_builder_method(kind, "get_executable_kind")

    def get_action_from_task_kind(self, kind: str, task_kind: str) -> str:
        """
        Get action from task.

        Parameters
        ----------
        kind : str
            Kind.
        task_kind : str
            Task kind.

        Returns
        -------
        str
            Action.
        """
        return self._call_builder_method(kind, "get_action_from_task_kind", task_kind)

    def get_task_kind_from_action(self, kind: str, action: str) -> list[str]:
        """
        Get task kinds from action.

        Parameters
        ----------
        kind : str
            Kind.
        action : str
            Action.

        Returns
        -------
        list of str
            Task kinds.
        """
        return self._call_builder_method(kind, "get_task_kind_from_action", action)

    def get_run_kind_from_action(self, kind: str, action: str) -> str:
        """
        Get run kind.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        str
            Run kind.
        """
        return self._call_builder_method(kind, "get_run_kind_from_action", action)

    def get_all_kinds(self, kind: str) -> list[str]:
        """
        Get all kinds.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        list of str
            All kinds.
        """
        return self._call_builder_method(kind, "get_all_kinds")

    def get_spec_validator(self, kind: str) -> SpecValidator:
        """
        Get spec validators.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        SpecValidator
            Spec validator.
        """
        return self._call_builder_method(kind, "get_spec_validator")

    @staticmethod
    def _get_kind(**kwargs) -> str:
        """
        Extract the 'kind' from parameters.

        Parameters
        ----------
        **kwargs
            Entity parameters.

        Returns
        -------
        str
            The kind of the entity.

        Raises
        ------
        BuilderError
            If 'kind' is not found in parameters.
        """
        try:
            return kwargs["kind"]
        except KeyError:
            raise BuilderError("Missing 'kind' parameter.")


# Global instance
entity_factory = EntityFactory()
