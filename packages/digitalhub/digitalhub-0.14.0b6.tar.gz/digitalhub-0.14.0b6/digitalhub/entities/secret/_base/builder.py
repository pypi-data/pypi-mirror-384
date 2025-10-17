# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.versioned.builder import VersionedBuilder
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.secret._base.entity import Secret
from digitalhub.entities.secret._base.spec import SecretSpec, SecretValidator
from digitalhub.entities.secret._base.status import SecretStatus


class SecretSecretBuilder(VersionedBuilder):
    """
    SecretSecretBuilder builder.
    """

    ENTITY_TYPE = EntityTypes.SECRET.value
    ENTITY_CLASS = Secret
    ENTITY_SPEC_CLASS = SecretSpec
    ENTITY_SPEC_VALIDATOR = SecretValidator
    ENTITY_STATUS_CLASS = SecretStatus
    ENTITY_KIND = EntityKinds.SECRET_SECRET.value

    def build(
        self,
        kind: str,
        project: str,
        name: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> Secret:
        """
        Create a new object.

        Parameters
        ----------
        project : str
            Project name.
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
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Secret
            Object instance.
        """
        name = self.build_name(name)
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=name,
            description=description,
            labels=labels,
        )
        path = f"secret://{name}"
        provider = "kubernetes"
        spec = self.build_spec(
            path=path,
            provider=provider,
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            project=project,
            name=name,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )
