import json
import logging
from datetime import datetime
from typing import List
from typing import Optional

from dateutil.relativedelta import relativedelta
from edp.redy.services.api import ApiService
from edp.redy.services.devices.constants import COST_PER_KWH_URL
from edp.redy.services.devices.constants import DEVICES_URL
from edp.redy.services.devices.constants import METERING_URL
from edp.redy.services.devices.constants import MODULE_URL
from edp.redy.services.devices.constants import MODULES_URL
from edp.redy.services.devices.models.devicemodel import Device
from edp.redy.services.devices.models.devicemodel import DeviceGroup
from edp.redy.services.devices.models.devicemodel import DeviceType
from edp.redy.services.devices.models.devicemodel import DeviceTypeMap
from edp.redy.services.devices.models.modulesmodel import HistoricVar
from edp.redy.services.devices.models.modulesmodel import Module
from edp.redy.services.devices.models.modulesmodel import Resolution

log = logging.getLogger(__name__)

DATETIME_DAY_FORMAT = '%Y-%m-%d'


class DevicesService:

    def __init__(self, api_service: ApiService) -> None:
        self._api_service = api_service

    async def get_house_devices(self, house_id) -> List[Device]:
        devices_list = (
            await self._api_service.get(DEVICES_URL.format(house_id=house_id))
        )
        return [Device.from_dict(device) for device in devices_list]

    async def get_house_modules(
        self,
        house_id,
        device_type: Optional[DeviceType] = None,
        category_id: Optional[str] = None,
        groups_or_filter: Optional[List[DeviceGroup]] = None,
        groups_not_filter: Optional[List[DeviceGroup]] = None
    ) -> List[Module]:

        params = {}

        if device_type and (
                device_type != DeviceType.Consumption or not category_id):
            device_type_def = DeviceTypeMap.map[device_type]
            params['groupsorfilter'] = json.dumps(
                groups_or_filter
                if groups_or_filter
                else device_type_def.groups
            )
            params['groupsnotfilter'] = json.dumps(
                groups_not_filter
                if groups_not_filter
                else device_type_def.nonGroups)

        if (
            device_type and
            device_type == DeviceType.Consumption and category_id
        ):
            params['categoryfilter'] = category_id

        if not device_type and not category_id and groups_or_filter:
            if groups_or_filter:
                params['groupsorfilter'] = json.dumps(groups_or_filter)
            if groups_not_filter:
                params['groupsnotfilter'] = json.dumps(groups_not_filter)

        modules_list = (
            await self._api_service.get(
                MODULES_URL.format(house_id=house_id),
                params=params
            )
        )['Modules']

        return Module.schema().load(modules_list, many=True)

    async def get_house_module_by_group(
        self,
        house_id,
        groups_or_filter: Optional[DeviceGroup] = None,
        *args,
        **kwargs
    ) -> Module:
        modules = await self.get_house_modules(
            house_id,
            [groups_or_filter],
            *args,
            **kwargs
        )
        return modules[0]

    async def get_house_module(self, house_id: str, module_id: str) -> Module:
        module = await self._api_service.get(
            MODULE_URL.format(house_id=house_id, module_id=module_id)
        )
        return Module.from_dict(module)

    async def get_smart_meter(self, house_id: str) -> Module:
        return await self.get_house_module_by_group(
            house_id=house_id,
            groups_or_filter=DeviceGroup.SmartEnergyMeter
        )

    async def get_energy_storage(self, house_id: str) -> Module:
        return await self.get_house_module_by_group(
            house_id=house_id,
            groups_or_filter=DeviceGroup.EnergyStorage
        )

    async def get_gas_meter(self, house_id: str) -> Module:
        return await self.get_house_module_by_group(
            house_id=house_id,
            groups_or_filter=DeviceGroup.GasMeter
        )

    async def get_injection_meter(self, house_id: str) -> Module:
        return await self.get_house_module_by_group(
            house_id=house_id,
            groups_or_filter=DeviceGroup.InjectionMeter
        )

    async def get_alerts_devices(self, house_id: str) -> Module:
        return await self.get_house_modules(
            house_id=house_id,
            groups_or_filter=[
                DeviceGroup.Metering,
                DeviceGroup.ConsumptionMeter
            ],
            groups_not_filter=[
                DeviceGroup.ProductionMeter,
                DeviceGroup.SmartEnergyMeter
            ]
        )

    async def get_cost_per_kwh(
        self,
        house_id: str,
        resolution: str,
        date: str
    ):
        cost = await self._api_service.get(
            COST_PER_KWH_URL.format(house_id=house_id),
            params={'date': date, 'resolution': resolution}
        )

        return cost

    @staticmethod
    def calculate_end(start: datetime, resolution: Resolution) -> datetime:
        delta = None
        if resolution == Resolution.QuarterHour:
            delta = relativedelta()
        elif resolution == Resolution.Hour:
            delta = relativedelta()
        elif resolution == Resolution.Day:
            delta = relativedelta(months=1, days=-1)
        elif resolution == Resolution.Month:
            delta = relativedelta(years=1, days=-1)
        else:
            raise ValueError(f'The resolution {resolution} is not supported')

        return start + delta

    @staticmethod
    def calculate_start(resolution: Resolution) -> datetime:
        now = datetime.now()

        if resolution in (Resolution.QuarterHour, Resolution.Hour):
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif resolution == Resolution.Day:
            now = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif resolution == Resolution.Month:
            now = now.replace(
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0)

        return now

    def date_to_string(self, date: datetime) -> str:
        return date.strftime(DATETIME_DAY_FORMAT)

    async def get_metering(
        self,
        house_id: str,
        device_id: str,
        module_id: str,
        resolution: Resolution,
        historicVar: HistoricVar,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ):
        if not start:
            start = self.calculate_start(resolution)
        if not end:
            end = self.calculate_end(start, resolution)

        params = {
            'start': self.date_to_string(start),
            'end': self.date_to_string(end),
            'resolution': resolution.value,
            'historicvar': historicVar.value
        }
        # log.info(f"get_metering params: {params}")
        metering = await self._api_service.get(
            METERING_URL.format(
                house_id=house_id,
                device_id=device_id,
                module_id=module_id
            ),
            params=params
        )

        return metering
