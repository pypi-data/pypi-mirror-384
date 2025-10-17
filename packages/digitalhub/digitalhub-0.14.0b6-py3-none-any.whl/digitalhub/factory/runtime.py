# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.factory.registry import registry

if typing.TYPE_CHECKING:
    from digitalhub.runtimes._base import Runtime


class RuntimeFactory:
    """
    Factory for creating and managing runtime builders.

    This class handles the creation of runtimes through their respective builders,
    using a centralized registry.
    """

    def build_runtime(self, kind_to_build_from: str, project: str) -> Runtime:
        """
        Build a runtime.

        Parameters
        ----------
        kind_to_build_from : str
            Runtime type.
        project : str
            Project name.

        Returns
        -------
        Runtime
            Runtime object.
        """
        builder = registry.get_runtime_builder(kind_to_build_from)
        return builder.build(project=project)


# Global instance
runtime_factory = RuntimeFactory()
