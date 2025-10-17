# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator


class WorkflowSpec(Spec):
    """
    WorkflowSpec specifications.
    """


class WorkflowValidator(SpecValidator):
    """
    WorkflowValidator validator.
    """
