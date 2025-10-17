# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.runtimes._base import Runtime


class RuntimeBuilder:
    """
    Builder class for instantiating runtime objects.

    This class implements the Builder pattern to create Runtime instances.
    Subclasses must set the RUNTIME_CLASS class variable to specify which
    Runtime implementation to build.

    Attributes
    ----------
    RUNTIME_CLASS : Runtime
        The Runtime class to be instantiated by this builder.

    Raises
    ------
    BuilderError
        If RUNTIME_CLASS is not set in the implementing class.
    """

    RUNTIME_CLASS: Runtime = None

    def __init__(self) -> None:
        """
        Initialize a RuntimeBuilder instance.

        Raises
        ------
        BuilderError
            If RUNTIME_CLASS is not set in the implementing class.
        """
        if self.RUNTIME_CLASS is None:
            raise BuilderError("RUNTIME_CLASS must be set")

    def build(self, project: str, *args, **kwargs) -> Runtime:
        """
        Build a runtime object.

        Parameters
        ----------
        project : str
            The project identifier for the runtime instance.
        *args
            Additional positional arguments to pass to the Runtime constructor.
        **kwargs
            Additional keyword arguments to pass to the Runtime constructor.

        Returns
        -------
        Runtime
            A new instance of the configured Runtime class.
        """
        return self.RUNTIME_CLASS(project, *args, **kwargs)
