from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase


class IDeviceType:
    ...


class DeviceType(IDeviceType, Enum):
    Consumption = 'consumption'
    Generation = 'generation'
    Climatization = 'climatization'
    Sensors = 'sensors'


class ClimatizationDeviceType(IDeviceType, Enum):
    Thermostat = 'Thermostat'
    AirConditioning = 'Air Conditioning'
    Temperature = 'Temperature'


class SensorsDeviceType(IDeviceType, Enum):
    DoorWindow = 'Door & Window'
    Flood = 'Flood'
    Smoke = 'Smoke'
    Motion = 'Motion'


class DeviceGroup(str, Enum):
    Metering = 'METERING'
    ConsumptionMeter = 'CONSUMPTION_METER'
    ProductionMeter = 'PRODUCTION_METER'
    InjectionMeter = 'INJECTION_METER'
    SmartEnergyMeter = 'SMART_ENERGY_METER'
    GasMeter = 'GAS_METER'
    EnergyStorage = 'ENERGY_STORAGE'
    Switch = 'SWITCH'
    BatterySupplied = 'BATTERY SUPPLIED'
    Thermostat = 'THERMOSTAT'
    TemperatureMeter = 'TEMPERATURE_METER'
    Hvac = 'HVAC'
    Detector = 'DETECTOR'
    DoorWindow = 'DOOR_WINDOW'
    Water = 'WATER'
    Fire = 'FIRE'
    Motion = 'MOTION'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Device:
    connection_state: bool
    creation_date: str
    device_id: str
    device_local_id: str
    firmware_version: str
    house_id: str
    last_communication: str
    model: str
    type: str


@dataclass_json
@dataclass
class TypeMap:
    order: int
    groups: List[DeviceGroup]
    nonGroups: List[DeviceGroup]
    properties: Optional[Dict[str, Any]] = None
    subtypes: Optional[Dict[IDeviceType, 'TypeMap']] = None


class ClimatizationDeviceTypesMap:
    map: Dict[IDeviceType, TypeMap] = {
        ClimatizationDeviceType.Temperature: TypeMap(
            order=1,
            groups=[DeviceGroup.TemperatureMeter],
            nonGroups=[],
            properties=dict(
                icon='/assets/img/icons/ic-sensor-temp.svg',
                connectivity=True
            )
        ),
        ClimatizationDeviceType.Thermostat: TypeMap(
            order=2,
            groups=[DeviceGroup.Thermostat],
            nonGroups=[DeviceGroup.Hvac],
            properties=dict(
                icon='/assets/img/icons/ic-thermostat.svg',
                connectivity=True
            )
        ),
        ClimatizationDeviceType.AirConditioning: TypeMap(
            order=3,
            groups=[DeviceGroup.Hvac],
            nonGroups=[],
            properties={}
        )
    }


class SensorsDeviceTypesMap:
    map: Dict[IDeviceType, TypeMap] = {
        SensorsDeviceType.DoorWindow: TypeMap(
            order=1,
            groups=[DeviceGroup.DoorWindow],
            nonGroups=[],
            properties={}
        ),
        SensorsDeviceType.Flood: TypeMap(
            order=2,
            groups=[DeviceGroup.Water],
            nonGroups=[],
            properties={}
        ),
        SensorsDeviceType.Smoke: TypeMap(
            order=3,
            groups=[DeviceGroup.Fire],
            nonGroups=[],
            subtypes={}
        ),
        SensorsDeviceType.Motion: TypeMap(
            order=4,
            groups=[DeviceGroup.Motion],
            nonGroups=[],
            subtypes={}
        )
    }


class DeviceTypeMap:
    map: Dict[DeviceType, TypeMap] = {
        DeviceType.Consumption: TypeMap(
            order=1,
            groups=[DeviceGroup.ConsumptionMeter, DeviceGroup.Switch],
            nonGroups=[
                DeviceGroup.SmartEnergyMeter,
                DeviceGroup.ProductionMeter
            ],
            properties={}
        ),
        DeviceType.Generation: TypeMap(
            order=2,
            groups=[DeviceGroup.ProductionMeter],
            nonGroups=[],
            properties={}
        ),
        DeviceType.Climatization: TypeMap(
            order=3,
            groups=[
                DeviceGroup.Thermostat,
                DeviceGroup.TemperatureMeter,
                DeviceGroup.Hvac
            ],
            nonGroups=[],
            subtypes=ClimatizationDeviceTypesMap.map
        ),
        DeviceType.Sensors: TypeMap(
            order=4,
            groups=[DeviceGroup.Detector],
            nonGroups=[],
            subtypes=SensorsDeviceTypesMap.map
        )
    }
