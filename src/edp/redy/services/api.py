"""Generic API."""
import logging
from typing import Any

import aiohttp
from aiohttp import client_exceptions as exceptions
from edp.redy.services.auth import AuthService

BASE_URL = "https://uiapi.redy.edp.com"
RETRIES = 3

log = logging.getLogger(__name__)


class ApiServiceError(Exception):
    """Base class for API Service related errors."""


class ResponseError(ApiServiceError):
    """The response error class."""

    def __init__(self, status: int, url: str, message: str, details: Any):
        """Create a response error object.

        Args:
            status (int): The status of the request
            url (str): The endpoint used in the request
            message (str): The message received as response
            details (Any): Any further details
        """
        self.status = status
        self.message = message
        self.url = url
        self.details = details

    def __str__(self) -> str:
        """Generate a string representation of the response error object.

        Returns:
            str: The string representation of ResponseError object.
        """
        return (
            f"{self.status}, url={self.url}, message={self.message}, "
            f"details={self.details}"
        )


class ApiService:
    """API Service class."""

    def __init__(self, auth: AuthService):
        """Initialize the API Service object."""
        self._auth = auth

    @property
    async def headers(self):
        """Headers being used in the requests.

        Returns:
            _type_: The headers
        """
        return {"authorization": await self._auth.cognito_user.id_token}

    async def start(self):
        """Start the instantiation of the API service."""
        ...

    async def stop(self):
        """Clear the instantiation of the API service."""
        ...

    async def get(self, url: str, *args, **kwargs):
        """Represent the API get method.

        Args:
            url (str): The endpoint to execute the get request
            *args: Optional arguments
            **kwargs: Optional keyword arguments

        Raises:
            ResponseError: The error returned if there's a problem

        Returns:
            _type_: The response
        """
        resp = None
        retries = RETRIES
        while retries:
            retries -= 1
            try:
                async with aiohttp.ClientSession() as session, session.get(
                    BASE_URL + url,
                    *args,
                    headers=await self.headers,
                    raise_for_status=True,
                    **kwargs,
                ) as response:
                    resp = await response.text()
                    response.raise_for_status()
                    return await response.json()
            except exceptions.ClientResponseError as ex:
                raise ResponseError(
                    status=ex.status,
                    url=str(ex.request_info.url),
                    message=ex.message,
                    details=resp,
                )
            except Exception:
                log.exception("Error:")
                await self._auth.cognito_user.authenticate()
