# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from requests.exceptions import HTTPError, RequestException

from digitalhub.utils.exceptions import (
    BackendError,
    BadRequestError,
    EntityAlreadyExistsError,
    EntityNotExistsError,
    ForbiddenError,
    MissingSpecError,
    UnauthorizedError,
)

if typing.TYPE_CHECKING:
    from requests import Response


class ErrorParser:
    """
    Parser for DHCore API errors.

    This class handles the parsing and translation of HTTP responses
    from the DHCore backend into appropriate Python exceptions.
    """

    @staticmethod
    def parse(response: Response) -> None:
        """
        Handle DHCore API errors.

        Parses the HTTP response and raises appropriate exceptions based on
        the status code and response content. Maps backend errors to specific
        exception types for better error handling in the client code.

        Parameters
        ----------
        response : Response
            The HTTP response object from requests.

        Raises
        ------
        TimeoutError
            If the request timed out.
        ConnectionError
            If unable to connect to the backend.
        MissingSpecError
            If the backend reports a missing spec (400 status).
        EntityAlreadyExistsError
            If the entity already exists (400 status with specific message).
        BadRequestError
            For other 400 status codes.
        UnauthorizedError
            For 401 status codes.
        ForbiddenError
            For 403 status codes.
        EntityNotExistsError
            For 404 status codes with specific message.
        BackendError
            For other 404 status codes and general backend errors.
        RuntimeError
            For unexpected exceptions.
        """
        try:
            response.raise_for_status()

        # Backend errors
        except RequestException as e:
            # Handle timeout
            if isinstance(e, TimeoutError):
                msg = "Request to DHCore backend timed out."
                raise TimeoutError(msg)

            # Handle connection error
            elif isinstance(e, ConnectionError):
                msg = "Unable to connect to DHCore backend."
                raise ConnectionError(msg)

            # Handle HTTP errors
            elif isinstance(e, HTTPError):
                txt_resp = f"Response: {response.text}."

                # Bad request
                if response.status_code == 400:
                    # Missing spec in backend
                    if "missing spec" in response.text:
                        msg = f"Missing spec in backend. {txt_resp}"
                        raise MissingSpecError(msg)

                    # Duplicated entity
                    elif "Duplicated entity" in response.text:
                        msg = f"Entity already exists. {txt_resp}"
                        raise EntityAlreadyExistsError(msg)

                    # Other errors
                    else:
                        msg = f"Bad request. {txt_resp}"
                        raise BadRequestError(msg)

                # Unauthorized errors
                elif response.status_code == 401:
                    msg = f"Unauthorized. {txt_resp}"
                    raise UnauthorizedError(msg)

                # Forbidden errors
                elif response.status_code == 403:
                    msg = f"Forbidden. {txt_resp}"
                    raise ForbiddenError(msg)

                # Entity not found
                elif response.status_code == 404:
                    # Put with entity not found
                    if "No such EntityName" in response.text:
                        msg = f"Entity does not exists. {txt_resp}"
                        raise EntityNotExistsError(msg)

                    # Other cases
                    else:
                        msg = f"Not found. {txt_resp}"
                        raise BackendError(msg)

                # Other errors
                else:
                    msg = f"Backend error. {txt_resp}"
                    raise BackendError(msg) from e

            # Other requests errors
            else:
                msg = f"Some error occurred. {e}"
                raise BackendError(msg) from e

        # Other generic errors
        except Exception as e:
            msg = f"Some error occurred: {e}"
            raise RuntimeError(msg) from e
