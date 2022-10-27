import logging
from typing import Optional
from uuid import uuid4

from awscrt import mqtt
from awscrt.auth import AwsCredentialsProvider
from awsiot import mqtt_connection_builder as mqtt_conn_builder
from edp.redy.services.auth import AuthService
from edp.redy.services.auth import REGION


IOT_CONN_HOST = 'axhipzdhdp7t3-ats.iot.' + REGION + '.amazonaws.com'

log = logging.getLogger(__name__)

# Callback when connection is accidentally lost.


def on_connection_interrupted(connection, error, **kwargs):
    log.warning(f'Connection interrupted. error: {error}')
    # TODO: Implement the mechanism to check if the token have expired, and
    # needs to disconnect and connect again with the new credentials

# Callback when an interrupted connection is re-established.


def on_connection_resumed(connection, return_code, session_present, **kwargs):
    log.info(
        f'Connection resumed. return_code: {return_code} session_present: '
        f'{session_present}')


class WebSocketMqtt:

    def __init__(self, auth: Optional[AuthService] = None) -> None:
        self._auth = auth or AuthService()
        self._con: Optional[mqtt.Connection] = None

    async def _credentials_provider(self):
        return AwsCredentialsProvider.new_static(
            access_key_id=await self._auth.cognito_identity.access_key_id,
            secret_access_key=await self._auth.cognito_identity.secret_key,
            session_token=await self._auth.cognito_identity.session_token
        )

    async def new_connection(
        self,
        endpoint: str = IOT_CONN_HOST,
        region: str = REGION,
        client_id: str = ''
    ) -> mqtt.Connection:
        if not client_id:
            client_id = f'Portal-{uuid4()}'
        if self._con is None:
            self._con = mqtt_conn_builder.websockets_with_default_aws_signing(
                endpoint=endpoint,
                region=region,
                credentials_provider=await self._credentials_provider(),
                on_connection_interrupted=on_connection_interrupted,
                on_connection_resumed=on_connection_resumed,
                client_id=client_id,
                clean_session=False,
                keep_alive_secs=30,
            )

        return self._con
