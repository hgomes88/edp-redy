import logging
from typing import Any

import aiohttp
from aiohttp import client_exceptions as exceptions
from edp.redy.services.auth import AuthService
from mypy_boto3_cognito_identity.client import Exceptions

BASE_URL = 'https://uiapi.redy.edp.com'
RETRIES = 3

log = logging.getLogger(__name__)


class ApiServiceError(Exception):
    """Base class for API Service related errors."""


class ResponseError(ApiServiceError):

    def __init__(self, status: int, url: str, message: str, details: Any):
        self.status = status
        self.message = message
        self.url = url
        self.details = details

    def __str__(self) -> str:
        return (
            f'{self.status}, url={self.url}, message={self.message}, '
            f'details={self.details}'
        )


class ApiService:

    def __init__(self, auth: AuthService):
        self._auth = auth
        self._cli = aiohttp.ClientSession()

    @property
    async def headers(self):
        return {
            'authorization': await self._auth.cognito_user.id_token
        }

    @property
    def client(self):
        return self._cli

    async def start(self):
        ...

    async def stop(self):
        ...

    async def get(self, url: str, *args, **kwargs):
        resp = None
        retries = RETRIES
        while retries:
            retries -= 1
            try:
                async with self._cli.get(
                    BASE_URL + url,
                    *args,
                    headers=await self.headers,
                    raise_for_status=True,
                    **kwargs
                ) as response:
                    resp = await response.text()
                    response.raise_for_status()
                    return await response.json()
            except exceptions.ClientResponseError as ex:
                raise ResponseError(
                    status=ex.status,
                    url=str(ex.request_info.url),
                    message=ex.message,
                    details=resp
                )
            except Exceptions.NotAuthorizedException:
                await self._auth.cognito_user.authenticate()
