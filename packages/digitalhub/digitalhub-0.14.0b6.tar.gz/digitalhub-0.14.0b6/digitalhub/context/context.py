# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import typing
from pathlib import Path

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.runtimes.enums import RuntimeEnvVar
from digitalhub.stores.client._base.enums import ApiCategories, BackendOperations
from digitalhub.utils.exceptions import BackendError

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project
    from digitalhub.stores.client._base.client import Client


class Context:
    """
    Context class built from a Project instance.

    Contains project-specific information and state, including project name,
    client instance, local context paths, and run-time information.

    Attributes
    ----------
    name : str
        The name of the project.
    client : BaseClient
        The client instance (local or remote) associated with the project.
    config : dict
        Project configuration profile.
    local : bool
        Whether the client is local or remote.
    root : Path
        The local context project path.
    is_running : bool
        Flag indicating if the context has an active run.
    _run_ctx : str | None
        Current run key, if any.
    """

    def __init__(self, project: Project) -> None:
        self.name: str = project.name
        self.client: Client = project._client
        self.config: dict = project.spec.config
        self.local: bool = project._client.is_local()
        self.root: Path = Path(project.spec.context)
        self.root.mkdir(parents=True, exist_ok=True)

        self.is_running: bool = False
        self._run_ctx: str | None = None
        self._search_run_ctx()

    def _search_run_ctx(self) -> None:
        """
        Search for an existing run id in env.
        """
        run_id = os.getenv(RuntimeEnvVar.RUN_ID.value)
        if run_id is not None:
            try:
                api = self.client.build_api(
                    category=ApiCategories.CONTEXT.value,
                    operation=BackendOperations.READ.value,
                    project=self.name,
                    entity_type=EntityTypes.RUN.value,
                    entity_id=run_id,
                )
                run_key = self.client.read_object(api=api)["key"]
                self.set_run(run_key)
            except BackendError:
                pass

    def set_run(self, run_ctx: str) -> None:
        """
        Set the current run key.

        Parameters
        ----------
        run_ctx : str
            The run key to set.
        """
        self.is_running = True
        self._run_ctx = run_ctx

    def unset_run(self) -> None:
        """
        Clear the current run key and reset running state.
        """
        self.is_running = False
        self._run_ctx = None

    def get_run_ctx(self) -> str | None:
        """
        Get the current run key.

        Returns
        -------
        str or None
            The current run key if set, None otherwise.
        """
        return self._run_ctx
