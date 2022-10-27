import asyncio
import json
from asyncio import Task
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from awscrt import mqtt
from edp.redy.logger.logger import logging
from edp.redy.services.auth import AuthService
from edp.redy.services.wsmqtt import WebSocketMqtt

log = logging.getLogger(__name__)


class DeviceType(str, Enum):
    REDYBOX = 'redybox'
    WIFI = 'wifi'


@dataclass
class StreamDevice:
    localId: str
    type: DeviceType


DEVICE_ITEMS = {
    DeviceType.REDYBOX: 'rb',
    DeviceType.WIFI: 'wifi'
}


class Stream:

    def __init__(self, auth: AuthService) -> None:
        self._qos = mqtt.QoS.AT_LEAST_ONCE
        self._auth = auth
        self._con: mqtt.Connection
        self._devices: List[StreamDevice] = []
        self._tasks: Dict[str, Task] = {}
        self._callback = self._on_message_received

    def add_devices(self, devices: List[StreamDevice]):
        """ Add a list of devices streaming the data from """

        self._devices = [
            device for device in devices if device.type in DEVICE_ITEMS]
        return self

    def add_callback(self, callback):
        self._callback = callback
        return self

    async def start(self):
        """ Start streaming """

        self._con = await self._create_connection()

        log.debug('Mqtt socket connection establishing...')
        # self._con.connect().result()
        await asyncio.wrap_future(self._con.connect())

        log.debug('Mqtt socket connection established')

        for device in self._devices:
            for topic in self._device_topics(device.localId):
                await self._subscribe(topic)

            self._tasks[device.localId] = asyncio.create_task(
                self._keep_connection_alive(device_id=device.localId)
            )

    async def stop(self):
        """ Stop streaming """

        self._con.unsubscribe()
        await asyncio.wrap_future(self._con.disconnect())

        for task in self._tasks.values():
            task.cancel()

        await asyncio.wrap_future(self._con.disconnect())

    async def _create_connection(self) -> mqtt.Connection:
        log.debug('Configuring the mqtt socket connection...')
        con = await WebSocketMqtt(auth=self._auth).new_connection()
        log.debug('Mqtt socket connection done')
        return con

    def _module_update_topic(self, device_id: str) -> str:
        return f'wifi/{device_id}/fromDev/module/update'

    def _module_changed_topic(self, device_id: str) -> str:
        return f'wifi/{device_id}/fromDev/module/changed'

    def _realtime_topic(self, device_id: str) -> str:
        return f'wifi/{device_id}/fromDev/realtime'

    def _device_topics(self, device_id: str) -> Tuple[str, str, str]:
        return (
            self._module_update_topic(device_id),
            self._module_changed_topic(device_id),
            self._realtime_topic(device_id)
        )

    def _device_req_topic(self, device_id: str):
        return f'wifi/{device_id}/toDev/realtime'

    def _on_message_received(self, topic, payload, dup, qos, retain, **kwargs):
        log.debug(f"Received message from topic '{topic}': {payload}")

    async def _subscribe(self, topic: str):
        log.debug(f"Subscribing to topic: '{topic}'...")
        await asyncio.wrap_future(
            self._con.subscribe(
                topic=topic,
                qos=self._qos,
                callback=self._callback
            )[0]
        )
        log.debug('Subscribing to topic done')

    async def _publish(self, topic: str, payload: dict):

        log.debug(f"Publishing the request to topic '{topic}': {payload}...")
        await asyncio.wrap_future(
            self._con.publish(
                topic=topic,
                payload=json.dumps(payload),
                qos=self._qos
            )[0]
        )
        log.debug('Publishing the realtime request done')

    async def _keep_connection_alive(
        self,
        device_id: str,
        period_s: float = 55
    ):
        while True:

            try:

                log.debug(f'Keeping connection alive for {device_id}')

                await self._publish(
                    topic=self._device_req_topic(device_id),
                    payload={
                        'id': self._con.client_id,
                        'operationType': 'realtime',
                        'messageType': 'request',
                        'data': {
                            'timeout': 60
                        }
                    }
                )
                await asyncio.sleep(period_s)

            except asyncio.exceptions.CancelledError:
                pass
            except BaseException:
                log.exception('Unexpected error')


class StreamCallbacks:

    @staticmethod
    def on_notification(operation_type: str, data: Dict[str, Any]):
        log.info(f"Notification '{operation_type}': {data}")

    @staticmethod
    def on_response(operation_type: str, success: bool, data: Dict[str, Any]):
        log.info(f"Response '{operation_type}'({success}): {data}")


class StreamService:

    def __init__(self, auth: AuthService) -> None:
        self._auth = auth
        self._stream = Stream(auth=self._auth)
        self._devices: List[StreamDevice] = []
        self._callback: Optional[StreamCallbacks] = None
        self._on_response_cb: Optional[Callable] = None
        self._on_notification_cb: Optional[Callable] = None

    def add_devices(self, devices: List[StreamDevice]) -> 'StreamService':
        self._devices = devices
        return self

    def add_callback_class(self, callback: StreamCallbacks) -> 'StreamService':
        self._callback = callback
        return self

    def add_callback(
            self,
            *,
            on_response_cb=None,
            on_notification_cb=None) -> 'StreamService':
        self._on_response_cb = on_response_cb
        self._on_notification_cb = on_notification_cb
        return self

    async def start(self) -> 'StreamService':
        await self._start_stream()
        return self

    async def stop(self):
        log.info('Real Time Streaming being stopped...')
        await self._stream.stop()
        log.info('Real Time Streaming stopped')

    async def _start_stream(self):
        # Configuring realtime connection
        log.info('Real Time Streaming being configured...')

        iot_devices: List[StreamDevice] = []

        for device in self._devices:
            if device.type in [dev_type.value for dev_type in DeviceType]:
                iot_devices.append(device)

        self._stream.add_devices(iot_devices)
        self._stream.add_callback(self._on_message_received)
        await self._stream.start()
        log.info('Real Time Streaming configured')

    def _on_message_received(
            self,
            topic,
            payload: bytes,
            dup,
            qos,
            retain,
            **kwargs):
        payload_data: Dict[str, Any] = json.loads(payload.decode())
        message_type = payload_data.get('messageType')

        if message_type == 'notification':
            operation_type = payload_data['operationType']
            data_list = payload_data['data']
            if self._callback:
                for data in data_list:
                    self._callback.on_notification(
                        operation_type=operation_type, data=data)
            elif self._on_notification_cb:
                for data in data_list:
                    self._on_notification_cb(
                        operation_type=operation_type, data=data)
            else:
                log.info(
                    f"Notification from topic {topic} '{operation_type}': "
                    f'{data_list}'
                )
        elif message_type == 'response':
            operation_type = payload_data['operationType']
            success = payload_data['success']
            data = payload_data['data']
            if self._callback:
                self._callback.on_response(
                    operation_type=operation_type, success=success, data=data)
            elif self._on_response_cb:
                self._on_response_cb(
                    operation_type=operation_type,
                    success=success,
                    data=data)
            else:
                log.info(
                    f"Response from topic {topic} '{operation_type}'"
                    f'({success}): {data}'
                )
        else:
            log.info(f'Unknown message type. Data: {payload_data}')
