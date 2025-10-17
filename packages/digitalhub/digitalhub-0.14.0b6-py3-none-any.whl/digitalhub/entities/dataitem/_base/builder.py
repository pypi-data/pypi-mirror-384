# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.versioned.builder import VersionedBuilder
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem


class DataitemBuilder(VersionedBuilder):
    """
    Dataitem builder.
    """

    ENTITY_TYPE = EntityTypes.DATAITEM.value

    def build(
        self,
        kind: str,
        project: str,
        name: str,
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
        """
        if path is None:
            raise EntityError("Path must be provided.")

        name = self.build_name(name)
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=name,
            description=description,
            labels=labels,
            embedded=embedded,
        )
        spec = self.build_spec(
            path=path,
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
