import asyncio
import functools
import logging
import os
from datetime import datetime
from typing import Any
from typing import Optional

import boto3
from mypy_boto3_cognito_identity.client import CognitoIdentityClient
from warrant import Cognito

REGION = 'eu-west-1'
COGNITO_USER_POOL_ID = REGION + '_' + '7qre3K7aN'
COGNITO_CLIENT_ID = '78fe04ngpmrualq67a5p59sbeb'
IOT_IDENTITY_POOL_ID = REGION + ':' + 'a9a52b46-1722-49a0-8f8b-e8532c12abef'
IOT_LOGIN = 'cognito-idp' + '.' + REGION + '.' + \
    'amazonaws.com' + '/' + COGNITO_USER_POOL_ID

log = logging.getLogger(__name__)

# The following environment variable need to be settled in order to prevent
# warning messages from AWS
os.environ['AWS_EC2_METADATA_DISABLED'] = 'true'


class AuthService:

    def __init__(
        self,
        cognito_user: Optional['CognitoUser'] = None,
        cognito_identity: Optional['CognitoIdentity'] = None
    ):
        """ Initialize the auth service """

        self._cognito_user = cognito_user or CognitoUser()
        self._cognito_identity = cognito_identity or CognitoIdentity(
            self._cognito_user)
        self._logged_in: bool = False

    @property
    def cognito_user(self):
        """ Returns the cognito user object. """

        return self._cognito_user

    @property
    def cognito_identity(self):
        """ Returns the cognito identity object. """

        return self._cognito_identity

    @property
    def logged_in(self):
        """ Returns whether the login was done or not. """

        return self._logged_in

    async def login(self, username: str, password: str):
        """ Login with the username and password given. """

        log.info('User login ongoing...')
        await self._cognito_user.login(username=username, password=password)
        self._logged_in = True
        log.info('User logged in')
        return self


class CognitoUser:

    def __init__(
        self,
        cognito_user: Optional[Cognito] = None,
        user_pool_id: str = COGNITO_USER_POOL_ID,
        client_id: str = COGNITO_CLIENT_ID,
        region: str = REGION

    ):
        """ Initialize the cognito user. """

        self._cognito_user = cognito_user or self._get_cognito_user()
        self._logged_in: bool = False
        self._user_pool_id = user_pool_id,
        self._client_id = client_id
        self._region = region
        self._auth_task: asyncio.Task
        self._password: str

    async def login(self, username: str, password: str):
        """ Authenticate user given the username and password. """

        self._cognito_user.username = username
        self._password = password
        await self.authenticate()
        self._auth_task = asyncio.create_task(self._authenticate_task())
        self._logged_in = True

    async def authenticate(self):
        await self._run_in_executor(
            self._cognito_user.authenticate,
            password=self._password
        )

    @property
    def logged_in(self):
        """ Returns whether the login was done or not. """

        return self._logged_in

    @property
    async def id_token(self):
        """ Returns the current cognito user id token.

            If token is expired, it will be automatically refreshed.
        """

        await self._check_token()
        return self._cognito_user.id_token

    @property
    async def access_token(self):
        """ Returns the current cognito user access token.

            If token is expired, it will be automatically refreshed.
        """

        await self._check_token()
        return self._cognito_user.access_token

    @property
    async def refresh_token(self):
        """ Returns the current cognito user refresh token.

            If token is expired, it will be automatically refreshed.
        """

        await self._check_token()
        return self._cognito_user.refresh_token

    async def _check_token(self):
        await self._run_in_executor(self._cognito_user.check_token, renew=True)

    def _get_cognito_user(self) -> Cognito:
        return Cognito(
            user_pool_id=self._user_pool_id,
            client_id=self._client_id,
            user_pool_region=self._region
        )

    async def _run_in_executor(self, func, *args, **kwargs) -> Any:
        return await asyncio.get_event_loop().run_in_executor(
            None,
            functools.partial(func, *args, **kwargs)
        )

    async def _authenticate_task(self):
        while True:
            try:
                # Re-authenticate after 55 min
                await asyncio.sleep(60 * 55)
                await self._run_in_executor(
                    self._cognito_user.authenticate,
                    password=self._password
                )
            except Exception:
                log.exception('Error: ')


class CognitoIdentity:

    def __init__(
        self,
        cognito_user: CognitoUser,
        cognito_identity: Optional[CognitoIdentityClient] = None,
        identity_id: str = IOT_IDENTITY_POOL_ID,
        login: str = IOT_LOGIN,
        region: str = REGION
    ):
        """ Initialize the cognito identity """

        self._cognito_user = cognito_user
        self._identity_id = identity_id
        self._login = login
        self._region = region
        self._cognito_identity = (
            cognito_identity or self._get_cognito_identity()
        )
        self._access_key_id = None
        self._secret_key = None
        self._session_token = None
        self._expiration = None

    @property
    async def access_key_id(self):
        """ Returns the current cognito identity access key.

            If token is expired, it will be automatically refreshed.
        """

        await self._check_token()
        return self._access_key_id

    @property
    async def secret_key(self):
        """ Returns the current cognito identity secret key.

            If token is expired, it will be automatically refreshed.
        """

        await self._check_token()
        return self._secret_key

    @property
    async def session_token(self):
        """ Returns the current cognito identity session token.

            If token is expired, it will be automatically refreshed.
        """

        await self._check_token()
        return self._session_token

    @property
    async def expiration(self):
        """ Returns the token expiration date.

            If token is expired, it will be automatically refreshed.
        """

        await self._check_token()
        return self._expiration

    async def _check_token(self, renew=True) -> bool:

        now = datetime.now().timestamp()
        if not self._session_token or now > self._expiration.timestamp():
            expired = True
            if renew:
                log.debug('Renewing Session token')
                await self._renew_access_token()
        else:
            expired = False
        return expired

    async def _renew_access_token(self):
        credentials = await self._get_identity_credentials()
        self._access_key_id = credentials['AccessKeyId']
        self._secret_key = credentials['SecretKey']
        self._session_token = credentials['SessionToken']
        self._expiration = credentials['Expiration'].astimezone()

    async def _get_identity_credentials(self):
        if not self._cognito_user.logged_in:
            raise RuntimeError('User is not logged in')
        token = await self._cognito_user.id_token
        ret = await self._run_in_executor(
            self._cognito_identity.get_credentials_for_identity,
            IdentityId=self._identity_id,
            Logins={self._login: token}
        )
        return ret['Credentials']

    def _get_cognito_identity(self) -> CognitoIdentityClient:
        return boto3.client(
            'cognito-identity',
            region_name=self._region,
        )

    async def _run_in_executor(self, func, *args, **kwargs) -> Any:
        return await asyncio.get_event_loop().run_in_executor(
            None, functools.partial(func, *args, **kwargs)
        )
