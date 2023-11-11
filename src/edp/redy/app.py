"""App module."""
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
from edp.redy.services.statevars.service import StateVariablesService
from edp.redy.services.stream import DeviceType
from edp.redy.services.stream import StreamDevice
from edp.redy.services.stream import StreamService
from marshmallow import fields
from typing_extensions import Protocol
from warrant import Cognito

log = logging.getLogger(__name__)

REGION = "eu-west-1"
USER_POOL_ID = REGION + "_" + "7qre3K7aN"
CLIENT_ID = "78fe04ngpmrualq67a5p59sbeb"
IDENTITY_POOL_ID = REGION + ":" + "a9a52b46-1722-49a0-8f8b-e8532c12abef"
IDENTITY_LOGIN = (
    "cognito-idp" + "." + REGION + "." + "amazonaws.com" + "/" + USER_POOL_ID
)


class App:
    """Redy app."""

    def __init__(
        self,
        houses_service: HousesService,
        energy_service: EnergyService,
        devices_service: DevicesService,
        statevars_service: StateVariablesService,
        stream_service: StreamService,
    ) -> None:
        """Construct the EDP Redy APP, using dependency injection.

        Args:
            houses_service (HousesService): _description_
            energy_service (EnergyService): _description_
            devices_service (DevicesService): _description_
            statevars_service (StateVariablesService): _description_
            stream_service (StreamService): _description_
        """
        self.stream = stream_service
        self.house_api = houses_service
        self.energy_api = energy_service
        self.devices_api = devices_service
        self.statevars_api = statevars_service
        self._started: bool = False

    async def start(self):
        """Start the app."""
        self.house: House = await self._get_house()
        self._modules: Dict[str, Module] = await self._get_modules()
        self._devices: Dict[str, Device] = await self._get_devices()
        self.production_meter: Module = await self._get_production_meter()
        self.injection_meter: Module = await self._get_injection_meter()

        self._energy: Energy = self._get_energy()
        self._power: Power = self._get_power()
        await self._power.start()

        self._started = True

    @property
    def energy(self):
        """Return the energy object."""
        return self._energy

    @property
    def power(self):
        """Return the power object."""
        return self._power

    @property
    def started(self):
        """Indicate whether the start have been called."""
        return self._started

    def _get_energy(self) -> "Energy":
        return Energy(
            consumed=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.injection_meter.device_id,
                module_id=self.injection_meter.module_id,
                historic_var=HistoricVar.ActiveEnergyConsumed,
            ),
            produced=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.production_meter.device_id,
                module_id=self.production_meter.module_id,
                historic_var=HistoricVar.ActiveEnergyProduced,
            ),
            injected=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.injection_meter.device_id,
                module_id=self.injection_meter.module_id,
                historic_var=HistoricVar.ActiveEnergyInjected,
            ),
            self_consumed=EnergyType(
                devices_api=self.devices_api,
                house_id=self.house.house_id,
                device_id=self.injection_meter.device_id,
                module_id=self.injection_meter.module_id,
                historic_var=HistoricVar.ActiveEnergySelfConsumed,
            ),
        )

    def _get_power(self) -> "Power":
        return Power(
            stream_api=self.stream,
            injection_module=self.injection_meter,
            injection_device=self._devices[self.injection_meter.device_id],
            production_module=self.production_meter,
            production_device=self._devices[self.production_meter.device_id],
        )

    async def _get_house(self) -> House:
        houses = await self.house_api.get_houses()
        return houses[0]

    async def _get_modules(self) -> Dict[str, Module]:
        modules = await self.devices_api.get_house_modules(house_id=self.house.house_id)
        return {module.module_id: module for module in modules}

    async def _get_devices(self) -> Dict[str, Device]:
        devices = await self.devices_api.get_house_devices(house_id=self.house.house_id)
        return {device.device_id: device for device in devices}

    async def _get_injection_meter(self):
        for module in self._modules.values():
            if (
                ModuleGroup.SmartEnergyMeter in module.groups
                and ModuleGroup.ConsumptionMeter.value in module.groups
            ):
                return module
        return None

    async def _get_production_meter(self):
        for module in self._modules.values():
            if (
                ModuleGroup.SmartEnergyMeter.value not in module.groups
                and ModuleGroup.ProductionMeter.value in module.groups
            ):
                return module
        return None


@dataclass_json
@dataclass
class ValueCost:
    """Value cost dataclass."""

    value: float
    cost: float


@dataclass_json
@dataclass
class ValueCostDate(ValueCost):
    """Value cost date dataclass."""

    date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )


@dataclass_json
@dataclass
class EnergyValues:
    """Energy values dataclass."""

    history: List[ValueCostDate]
    total: ValueCost


class EnergyType:
    """Energy type class."""

    def __init__(
        self,
        devices_api: DevicesService,
        house_id: str,
        device_id: str,
        module_id: str,
        historic_var=HistoricVar,
    ) -> None:
        """Ini the energy type object."""
        self._devices_api = devices_api
        self._house_id = house_id
        self._device_id = device_id
        self._module_id = module_id
        self._historic_var = historic_var
        self._key = self._get_key()

    async def today(self, resolution: Resolution = Resolution.Hour) -> EnergyValues:
        """Return the energy values of the current day."""
        supported_resolutions = [Resolution.Hour, resolution.QuarterHour]
        if resolution not in supported_resolutions:
            raise ValueError(
                f"Resolution '{resolution}' is not supported. "
                f"Only {supported_resolutions} are supported"
            )
        return await self.in_dates(resolution, None, None)

    async def this_month(self) -> EnergyValues:
        """Return the energy values of the current month."""
        return await self.in_dates(Resolution.Day, None, None)

    async def this_year(self) -> EnergyValues:
        """Return the energy values of the current year."""
        return await self.in_dates(Resolution.Month, None, None)

    async def in_dates(
        self,
        resolution: Resolution,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> EnergyValues:
        """Return the energy values between the specified dates."""
        return await self._get_metering(resolution, start, end)

    async def to_json(self, indent=None):
        """Convert to json."""
        pass

    async def _get_metering(
        self, resolution: Resolution, start: Optional[datetime], end: Optional[datetime]
    ) -> EnergyValues:
        energy = await self._devices_api.get_metering(
            house_id=self._house_id,
            device_id=self._device_id,
            module_id=self._module_id,
            resolution=resolution,
            historicVar=self._historic_var,
            start=start,
            end=end,
        )
        return self._to_energy_values(energy, resolution)

    def _to_energy_values(self, energy, resolution: Resolution) -> EnergyValues:
        DATETIME_HOUR_FORMAT = "%Y-%m-%d %H:%M:%S"
        DATETIME_DAY_FORMAT = "%Y-%m-%d"
        DATETIME_MONTH_FORMAT = "%Y-%m"

        if resolution in (Resolution.Hour, Resolution.QuarterHour):
            format = DATETIME_HOUR_FORMAT
        elif resolution == Resolution.Day:
            format = DATETIME_DAY_FORMAT
        elif resolution == Resolution.Month:
            format = DATETIME_MONTH_FORMAT
        else:
            format = DATETIME_HOUR_FORMAT

        history: List = energy["energyChart"]
        totals: Dict = energy["totals"]

        new_totals = ValueCost(
            value=totals["value"][self._key], cost=totals["cost"][self._key]
        )

        new_history = []
        # now = datetime.now()
        for item in history:
            date = datetime.strptime(item["date"], format)
            if item["value"]:
                new_history.append(
                    ValueCostDate(
                        value=item["value"][self._key],
                        cost=item["cost"][self._key] if item["cost"] else 0,
                        date=date,
                    )
                )
            # elif date <= now:
            #     new_history.append(
            #         ValueCostDate(value=0, cost=0, date=date)
            #     )

        return EnergyValues(history=new_history, total=new_totals)

    def _get_key(self) -> str:
        if self._historic_var == HistoricVar.ActiveEnergyConsumed:
            return "N"
        return "D"


@dataclass
class Energy:
    """Energy dataclass."""

    produced: EnergyType
    self_consumed: EnergyType
    injected: EnergyType
    consumed: EnergyType


class PowerTypeCallback(Protocol):
    """Power type callback class."""

    async def __call__(self, value: float) -> None:
        """Caller for the power type callback."""
        ...


class PowerType:
    """Power type class."""

    def __init__(self) -> None:
        """Init power type object."""
        self.value = None
        self.date = None
        self._cb: Optional[PowerTypeCallback] = None

    def stream(self, callback: PowerTypeCallback):
        """Start stream."""
        self._cb = callback

    async def _callback(self, value):
        self.value = value
        self.date = datetime.now()
        if self._cb:
            await self._cb(value)


class Power:
    """Power class."""

    def __init__(
        self,
        stream_api: StreamService,
        injection_module: Module,
        injection_device: Device,
        production_module: Module,
        production_device: Device,
    ) -> None:
        """Initialize the power object.

        Args:
            stream_api (StreamService): The stream api to
            injection_module (Module): _description_
            injection_device (Device): _description_
            production_module (Module): _description_
            production_device (Device): _description_
        """
        self._stream_api = stream_api
        self._injection_module: Module = injection_module
        self._injection_device: Device = injection_device
        self._production_module: Module = production_module
        self._production_device: Device = production_device

        self.solar_produced = PowerType()
        self.solar_consumed = PowerType()
        self.grid_injected = PowerType()
        self.grid_consumed = PowerType()
        self.total_consumed = PowerType()

        self._callbacks = {
            self._injection_module.module_local_id: {
                "emeter:power_aplus": self.grid_consumed._callback,
                "emeter:power_aminus": self.grid_injected._callback,
            },
            self._production_module.module_local_id: {
                "emeter:power_aminus": self.solar_produced._callback
            },
        }

    async def start(self):
        """Start the EDP Redy app."""
        await self._start_start_stream()

    async def _start_start_stream(self):
        await self._stream_api.add_devices(
            [
                StreamDevice(
                    localId=self._injection_device.device_local_id,
                    type=DeviceType(self._injection_device.type),
                ),
                StreamDevice(
                    localId=self._production_device.device_local_id,
                    type=DeviceType(self._production_device.type),
                ),
            ]
        ).add_callback(
            on_notification_cb=self._on_notification, on_response_cb=self._on_response
        ).start()

    async def _on_notification(self, operation_type: str, data: Dict[str, Any]):
        module_local_id: str = data["localId"]
        state_variables: Dict[str, Any] = data["stateVariables"]

        if module_local_id in self._callbacks:
            supported_callbacks = self._callbacks[module_local_id]
            for name, value in state_variables.items():
                if name in supported_callbacks:
                    await supported_callbacks[name](value)

            # If there was any change, calculate and update the self consumed
            if (
                self.solar_produced.value is not None
                and self.grid_injected.value is not None
            ):
                solar_consumed = self.solar_produced.value - self.grid_injected.value
                await self.solar_consumed._callback(solar_consumed)

            if (
                self.solar_consumed.value is not None
                and self.grid_consumed.value is not None
            ):
                total_consumed = self.solar_consumed.value + self.grid_consumed.value
                await self.total_consumed._callback(total_consumed)

    async def _on_response(
        self, operation_type: str, success: bool, data: Dict[str, Any]
    ):
        pass


def get_cognito(user_pool_id, client_id, region) -> Cognito:
    """Get cognito."""
    return Cognito(
        user_pool_id=user_pool_id,
        client_id=client_id,
        user_pool_region=region,
    )


def get_cognito_user(cognito: Cognito) -> CognitoUser:
    """Get cognito user."""
    return CognitoUser(
        cognito_user=cognito,
        user_pool_id=cognito.user_pool_id,
        client_id=cognito.client_id,
        region=cognito.user_pool_region,
    )


def get_cognito_identity(
    cognito_user: CognitoUser, identity_id, identity_login
) -> CognitoIdentity:
    """Get cognito identity."""
    return CognitoIdentity(
        cognito_user=cognito_user,
        cognito_identity=boto3.client(
            "cognito-identity",
            region_name=cognito_user._region,
        ),
        identity_id=identity_id,
        login=identity_login,
        region=cognito_user._region,
    )


def get_auth_service(
    cognito_user: CognitoUser, cognito_identity: CognitoIdentity
) -> AuthService:
    """Get auth service."""
    return AuthService(cognito_user=cognito_user, cognito_identity=cognito_identity)


def get_api_service(auth_service: AuthService) -> ApiService:
    """Get api service."""
    return ApiService(auth=auth_service)


def get_api_stream(auth_service: AuthService) -> StreamService:
    """Get stream service."""
    return StreamService(auth_service)


def get_houses_service(api_service: ApiService) -> HousesService:
    """Get houses service."""
    return HousesService(api_service=api_service)


def get_devices_service(api_service: ApiService) -> DevicesService:
    """Get devices service."""
    return DevicesService(api_service=api_service)


def get_energy_service(api_service: ApiService) -> EnergyService:
    """Get energy service."""
    return EnergyService(api_service=api_service)


def get_statevars_service(api_service: ApiService) -> StateVariablesService:
    """Get state variables service."""
    return StateVariablesService(api_service=api_service)


async def get_app(
    username: str,
    password: str,
    user_pool_id: Optional[str] = USER_POOL_ID,
    client_id: Optional[str] = CLIENT_ID,
    region: Optional[str] = REGION,
    identity_pool_id: Optional[str] = IDENTITY_POOL_ID,
    identity_login: Optional[str] = IDENTITY_LOGIN,
) -> App:
    """Get redy app object."""

    user_pool_id = user_pool_id or USER_POOL_ID
    client_id = client_id or CLIENT_ID
    region = region or REGION
    identity_pool_id = identity_pool_id or IDENTITY_POOL_ID
    identity_login = identity_login or IDENTITY_LOGIN

    cognito = get_cognito(user_pool_id, client_id, region)
    cognito_user = get_cognito_user(cognito)
    cognito_identity = get_cognito_identity(
        cognito_user, identity_pool_id, identity_login
    )
    auth_service = get_auth_service(cognito_user, cognito_identity)
    await auth_service.login(username, password)

    api_service = get_api_service(auth_service)
    houses_service = get_houses_service(api_service)
    energy_service = get_energy_service(api_service)
    devices_service = get_devices_service(api_service)
    statevars_service = get_statevars_service(api_service)

    stream_service = get_api_stream(auth_service)

    return App(
        houses_service,
        energy_service,
        devices_service,
        statevars_service,
        stream_service,
    )
