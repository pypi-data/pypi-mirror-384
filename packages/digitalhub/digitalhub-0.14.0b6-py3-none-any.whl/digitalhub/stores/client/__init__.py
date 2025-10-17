# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""
Client module for DigitalHub SDK.

This module provides client implementations for interacting with different
backends:
- Local client for in-memory operations
- DHCore client for remote backend communication

The main entry point is through the get_client function which returns
the appropriate client instance based on the configuration.
"""
