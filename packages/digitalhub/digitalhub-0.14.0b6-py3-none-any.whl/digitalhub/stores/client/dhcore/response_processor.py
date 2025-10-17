# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from requests.exceptions import JSONDecodeError

from digitalhub.stores.client.dhcore.error_parser import ErrorParser
from digitalhub.utils.exceptions import BackendError, ClientError

if typing.TYPE_CHECKING:
    from requests import Response


# API levels that are supported
MAX_API_LEVEL = 20
MIN_API_LEVEL = 14
LIB_VERSION = 14


class ResponseProcessor:
    """
    Processes and validates HTTP responses from DHCore backend.

    Handles API version validation, error parsing, and response body parsing
    to dictionary. Supports API versions {MIN_API_LEVEL} to {MAX_API_LEVEL}.
    """

    def __init__(self) -> None:
        self._error_parser = ErrorParser()

    def process(self, response: Response) -> dict:
        """
        Process HTTP response with validation and parsing.

        Performs API version compatibility check, error parsing for failed
        responses, and JSON deserialization.

        Parameters
        ----------
        response : Response
            HTTP response object from backend.

        Returns
        -------
        dict
            Parsed response body as dictionary.
        """
        self._check_api_version(response)
        self._error_parser.parse(response)
        return self._parse_json(response)

    def _check_api_version(self, response: Response) -> None:
        """
        Validate DHCore API version compatibility.

        Checks backend API version against supported range and warns if backend
        version is newer than library. Supported: {MIN_API_LEVEL} to {MAX_API_LEVEL}.

        Parameters
        ----------
        response : Response
            HTTP response containing X-Api-Level header.
        """
        if "X-Api-Level" not in response.headers:
            return

        core_api_level = int(response.headers["X-Api-Level"])
        if not (MIN_API_LEVEL <= core_api_level <= MAX_API_LEVEL):
            raise ClientError("Backend API level not supported.")

        if LIB_VERSION < core_api_level:
            warn("Backend API level is higher than library version. You should consider updating the library.")

    @staticmethod
    def _parse_json(response: Response) -> dict:
        """
        Parse HTTP response body to dictionary.

        Converts JSON response to Python dictionary, treating empty responses
        as valid and returning empty dict.

        Parameters
        ----------
        response : Response
            HTTP response object to parse.

        Returns
        -------
        dict
            Parsed response body as dictionary, or empty dict if body is empty.
        """
        try:
            return response.json()
        except JSONDecodeError:
            if response.text == "":
                return {}
            raise BackendError("Backend response could not be parsed.")
