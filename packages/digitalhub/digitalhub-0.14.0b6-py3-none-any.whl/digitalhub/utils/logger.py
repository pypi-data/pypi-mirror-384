# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging

# Create logger
LOGGER = logging.getLogger("digitalhub-core")
LOGGER.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Create console handler and set formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Set console handler to the logger
LOGGER.addHandler(console_handler)
