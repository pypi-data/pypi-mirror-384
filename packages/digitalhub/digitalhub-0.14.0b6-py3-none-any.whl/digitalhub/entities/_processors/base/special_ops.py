# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.stores.client.api import get_client

if typing.TYPE_CHECKING:
    pass


class BaseEntitySpecialOpsProcessor:
    """
    Processor for specialized base entity operations.

    Handles backend operations like sharing, key building, and other
    specialized functionality for base-level entities.
    """

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
        client = get_client(kwargs.pop("local", False))
        return client.build_key(ApiCategories.BASE.value, entity_id)

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
        client = get_client(kwargs.pop("local", False))
        api = client.build_api(
            ApiCategories.BASE.value,
            BackendOperations.SHARE.value,
            entity_type=entity_type,
            entity_name=entity_name,
        )

        user = kwargs.pop("user", None)
        if unshare := kwargs.pop("unshare", False):
            users = client.read_object(api, **kwargs)
            for u in users:
                if u["user"] == user:
                    kwargs["id"] = u["id"]
                break
            else:
                raise ValueError(f"User '{user}' does not have access to project.")

        kwargs = client.build_parameters(
            ApiCategories.BASE.value,
            BackendOperations.SHARE.value,
            unshare=unshare,
            user=user,
            **kwargs,
        )
        if unshare:
            client.delete_object(api, **kwargs)
            return
        client.create_object(api, obj={}, **kwargs)
