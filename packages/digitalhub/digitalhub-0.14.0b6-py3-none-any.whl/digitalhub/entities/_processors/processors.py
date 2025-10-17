# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._processors.base.processor import BaseEntityOperationsProcessor
from digitalhub.entities._processors.context.processor import ContextEntityOperationsProcessor

# Base processor singleton instance
base_processor = BaseEntityOperationsProcessor()

# Context processor singleton instance
context_processor = ContextEntityOperationsProcessor()
