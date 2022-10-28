import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
from dataclasses_json import config
from dataclasses_json import dataclass_json
from edp.redy.services.api import ApiService
from edp.redy.services.auth import AuthService
from edp.redy.services.auth import CognitoIdentity
from edp.redy.services.auth import CognitoUser
from edp.redy.services.devices.models.devicemodel import Device
from edp.redy.services.devices.models.modulesmodel import HistoricVar
from edp.redy.services.devices.models.modulesmodel import Module
from edp.redy.services.devices.models.modulesmodel import ModuleGroup
from edp.redy.services.devices.models.modulesmodel import Resolution
from edp.redy.services.devices.service import DevicesService
from edp.redy.services.energy.service import EnergyService
from edp.redy.services.houses.models.housemodel import House
from edp.redy.services.houses.service import HousesService
from edp.redy.services.stream import DeviceType
from edp.redy.services.stream import StreamDevice
from edp.redy.services.stream import StreamService
from marshmallow import fields
from typing_extensions import Protocol
from warrant import Cognito

log = logging.getLogger(__name__)


class App:

    def __init__(
        self,
        username: str,
        password: str,
        user_pool_id: str,
        client_id: str,
        region: str,
        identity_id: str,
        identity_login: str
    ) -> None:
        self._username = username
        self._password = password
        self._user_pool_id = user_pool_id
        self._client_id = client_id
        self._region = region
        self._identity_id = identity_id
        self._identity_login = identity_login

    async def start(self):
        self._auth = await self._login()
        self._api = self._get_api()
        self.house_api = HousesService(api_service=self._api)
        self.energy_api = EnergyService(api_service=self._api)
        self.devices_api = DevicesService(api_service=self._api)
        self.stream_api = StreamService(self._auth)

        self.house: House = await self._get_house()
        self._modules: Dict[str, Module] = await self._get_modules()
        self._devices: Dict[str, Device] = await self._get_devices()
        self.production_meter: Module = await self._get_production_meter()
        self.injection_meter: Module = await self._get_injection_meter()

        self._energy: Energy = self._get_energy()
        self._power: Power = self._get_power()
        await self._power.start()

    @property
    def energy(self):
        return self._energy

    @property
    def power(self):
        return self._power

    def _get_energy(self) -> 'Energy':
        return Energy(
            consumed=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.injection_meter.device_id,
                module_id=self.injection_meter.module_id,
                historic_var=HistoricVar.ActiveEnergyConsumed
            ),
            produced=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.production_meter.device_id,
                module_id=self.production_meter.module_id,
                historic_var=HistoricVar.ActiveEnergyProduced
            ),
            injected=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.injection_meter.device_id,
                module_id=self.injection_meter.module_id,
                historic_var=HistoricVar.ActiveEnergyInjected
            ),
            self_consumed=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.injection_meter.device_id,
                module_id=self.injection_meter.module_id,
                historic_var=HistoricVar.ActiveEnergySelfConsumed
            )
        )

    def _get_power(self) -> 'Power':
        return Power(
            stream_api=self.stream_api,
            injection_module=self.injection_meter,
            injection_device=self._devices[self.injection_meter.device_id],
            production_module=self.production_meter,
            production_device=self._devices[self.production_meter.device_id]
        )

    async def _login(self) -> AuthService:
        auth = self._get_auth()
        await auth.login(
            username=self._username,
            password=self._password
        )
        return auth

    def _get_api(self) -> ApiService:
        return ApiService(auth=self._auth)

    def _get_auth(self) -> AuthService:
        cognito_user = CognitoUser(
            cognito_user=Cognito(
                user_pool_id=self._user_pool_id,
                client_id=self._client_id,
                user_pool_region=self._region
            ),
            user_pool_id=self._user_pool_id,
            client_id=self._client_id,
            region=self._region
        )

        cognito_identity = CognitoIdentity(
            cognito_user=cognito_user,
            cognito_identity=boto3.client(
                'cognito-identity',
                region_name=self._region,
            ),
            identity_id=self._identity_id,
            login=self._identity_login,
            region=self._region
        )

        return AuthService(
            cognito_user=cognito_user,
            cognito_identity=cognito_identity
        )

    async def _get_house(self) -> House:
        houses = await self.house_api.get_houses()
        return houses[0]

    async def _get_modules(self) -> Dict[str, Module]:
        modules = await self.devices_api.get_house_modules(
            house_id=self.house.house_id
        )
        return {module.module_id: module for module in modules}

    async def _get_devices(self) -> Dict[str, Device]:
        devices = await self.devices_api.get_house_devices(
            house_id=self.house.house_id
        )
        return {device.device_id: device for device in devices}

    async def _get_injection_meter(self):
        for module in self._modules.values():
            if ModuleGroup.SmartEnergyMeter in module.groups and \
                    ModuleGroup.ConsumptionMeter.value in module.groups:
                return module
        return None

    async def _get_production_meter(self):
        for module in self._modules.values():
            if ModuleGroup.SmartEnergyMeter.value not in module.groups and \
                    ModuleGroup.ProductionMeter.value in module.groups:
                return module
        return None


@dataclass_json
@dataclass
class ValueCost:
    value: float
    cost: float


@dataclass_json
@dataclass
class ValueCostDate(ValueCost):
    date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        )
    )


@dataclass_json
@dataclass
class EnergyValues:
    history: List[ValueCostDate]
    total: ValueCost


class EnergyType:

    def __init__(self,
                 devices_api: DevicesService,
                 house_id: str,
                 device_id: str,
                 module_id: str,
                 historic_var=HistoricVar
                 ) -> None:
        self._devices_api = devices_api
        self._house_id = house_id
        self._device_id = device_id
        self._module_id = module_id
        self._historic_var = historic_var
        self._key = self._get_key()

    @property
    async def today(self) -> EnergyValues:
        return await self.in_dates(Resolution.Hour, None, None)

    @property
    async def this_month(self) -> EnergyValues:
        return await self.in_dates(Resolution.Day, None, None)

    @property
    async def this_year(self) -> EnergyValues:
        return await self.in_dates(Resolution.Month, None, None)

    async def in_dates(
        self,
        resolution: Resolution,
        start: Optional[datetime],
        end: Optional[datetime]
    ) -> EnergyValues:
        return await self._get_metering(resolution, start, end)

    async def to_json(self, indent=None):
        pass

    async def _get_metering(
        self,
        resolution: Resolution,
        start: Optional[datetime],
        end: Optional[datetime]
    ) -> EnergyValues:
        energy = await self._devices_api.get_metering(
            house_id=self._house_id,
            device_id=self._device_id,
            module_id=self._module_id,
            resolution=resolution,
            historicVar=self._historic_var,
            start=start,
            end=end
        )
        return self._to_energy_values(energy, resolution)

    def _to_energy_values(
            self,
            energy,
            resolution: Resolution) -> EnergyValues:

        DATETIME_HOUR_FORMAT = '%Y-%m-%d %H:%M:%S'
        DATETIME_DAY_FORMAT = '%Y-%m-%d'
        DATETIME_MONTH_FORMAT = '%Y-%m'

        if resolution in (Resolution.Hour, Resolution.QuarterHour):
            format = DATETIME_HOUR_FORMAT
        elif resolution == Resolution.Day:
            format = DATETIME_DAY_FORMAT
        elif resolution == Resolution.Month:
            format = DATETIME_MONTH_FORMAT
        else:
            format = DATETIME_HOUR_FORMAT

        history: List = energy['energyChart']
        totals: Dict = energy['totals']

        new_totals = ValueCost(
            value=totals['value'][self._key],
            cost=totals['cost'][self._key]
        )

        new_history = [
            ValueCostDate(
                value=item['value'][self._key],
                cost=item['cost'][self._key],
                date=datetime.strptime(item['date'], format)
            )
            for item in history if item['value']
        ]

        return EnergyValues(
            history=new_history,
            total=new_totals
        )

    def _get_key(self) -> str:
        if self._historic_var == HistoricVar.ActiveEnergyConsumed:
            return 'N'
        return 'D'


@dataclass
class Energy:
    produced: EnergyType
    self_consumed: EnergyType
    injected: EnergyType
    consumed: EnergyType


class PowerTypeCallback(Protocol):
    async def __call__(self, value: float) -> None:
        ...


class PowerType:
    def __init__(self) -> None:
        self.value = None
        self.date = None
        self._cb: Optional[PowerTypeCallback] = None

    def stream(self, callback: PowerTypeCallback):
        self._cb = callback

    async def _callback(self, value):
        self.value = value
        self.date = datetime.now()
        if self._cb:
            await self._cb(value)


class Power:
    def __init__(
        self,
        stream_api: StreamService,
        injection_module: Module,
        injection_device: Device,
        production_module: Module,
        production_device: Device
    ) -> None:
        self._stream_api = stream_api
        self._injection_module: Module = injection_module
        self._injection_device: Device = injection_device
        self._production_module: Module = production_module
        self._production_device: Device = production_device

        self.produced = PowerType()
        self.self_consumed = PowerType()
        self.injected = PowerType()
        self.consumed = PowerType()

        self._callbacks = {
            self._injection_module.module_local_id: {
                'emeter:power_aplus': self.consumed._callback,
                'emeter:power_aminus': self.injected._callback
            },
            self._production_module.module_local_id: {
                'emeter:power_aminus': self.produced._callback
            }
        }

    async def start(self):
        await self._start_start_stream()

    async def _start_start_stream(self):
        await self._stream_api.add_devices(
            [
                StreamDevice(
                    localId=self._injection_device.device_local_id,
                    type=DeviceType(self._injection_device.type)
                ),
                StreamDevice(
                    localId=self._production_device.device_local_id,
                    type=DeviceType(self._production_device.type)
                )
            ]
        ).add_callback(
            on_notification_cb=self._on_notification,
            on_response_cb=self._on_response
        ).start()

    async def _on_notification(
        self,
        operation_type: str,
        data: Dict[str, Any]
    ):
        module_local_id: str = data['localId']
        state_variables: Dict[str, Any] = data['stateVariables']

        if module_local_id in self._callbacks:
            supported_callbacks = self._callbacks[module_local_id]
            for name, value in state_variables.items():
                if name in supported_callbacks:
                    await supported_callbacks[name](value)

            # If there was any change, calculate and update the self consumed
            if (
                self.produced.value is not None and
                self.injected.value is not None
            ):
                self_consumed = self.produced.value - self.injected.value
                await self.self_consumed._callback(self_consumed)

    async def _on_response(
        self,
        operation_type: str,
        success: bool,
        data: Dict[str, Any]
    ):
        pass
