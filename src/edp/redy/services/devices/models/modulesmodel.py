from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase
from dataclasses_json import Undefined


def case_field(case: LetterCase, *args, **kwargs):
    return field(
        *args,
        metadata={'dataclasses_json': {'letter_case': case}},
        **kwargs
    )


def pascal_field(*args, **kwargs):
    return case_field(LetterCase.PASCAL, *args, **kwargs)


def camel_field(*args, **kwargs):
    return case_field(LetterCase.CAMEL, *args, **kwargs)


class ModuleGroup(str, Enum):
    SmartEnergyMeter = 'SMART_ENERGY_METER'
    ConsumptionMeter = 'CONSUMPTION_METER'
    ProductionMeter = 'PRODUCTION_METER'
    InjectionMeter = 'INJECTION_METER'
    Metering = 'METERING'
    VoltageMeter = 'VOLTAGE_METER'


class Resolution(str, Enum):
    QuarterHour = 'Q'
    Hour = 'H'
    Day = 'D'
    Month = 'M'


class HistoricVar(str, Enum):
    ActiveEnergyInjected = 'ActiveEnergyInjected'
    ActiveEnergyConsumed = 'ActiveEnergyConsumed'
    ActivePeakPowerConsumed = 'ActivePeakPowerConsumed'
    AverageVoltage = 'AverageVoltage'
    ActiveEnergySelfConsumed = 'ActiveEnergySelfconsumed'
    ActiveEnergyInjectedRaw = 'ActiveEnergyInjectedRaw'
    ActiveEnergyProduced = 'ActiveEnergyProduced'


class StateVar(str, Enum):
    ActivePowerAPlus = 'activePowerAplus'
    TotalActiveEnergyAPlus = 'totalActiveEnergyAplus'
    ActivePowerAMinus = 'activePowerAminus'
    TotalActiveEnergyAMinus = 'totalActiveEnergyAminus'
    Voltage = 'voltage'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class VoltageHistory:
    period: int
    unit: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class EnergyHistory:
    period: float
    unit: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ActiveEnergy:
    value: float
    unit: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Power:
    unit: str
    value: Optional[float] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Voltage:
    value: float
    unit: str


@dataclass_json(letter_case=LetterCase.PASCAL, undefined=Undefined.EXCLUDE)
@dataclass
class HistoricVars:
    supported: List[str] = camel_field()
    average_voltage: Optional[VoltageHistory] = None
    active_energy_produced: Optional[EnergyHistory] = None
    active_energy_injected_raw: Optional[EnergyHistory] = None
    active_energy_injected: Optional[EnergyHistory] = None
    active_energy_self_consumed: Optional[EnergyHistory] = None
    active_eak_power_consumed: Optional[EnergyHistory] = None
    active_energy_consumed: Optional[EnergyHistory] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class StateVars:
    supported: List[str]
    voltage: Voltage
    active_power_aminus: Optional[Power] = None
    active_power_aplus: Optional[Power] = None
    total_active_energy_aminus: Optional[ActiveEnergy] = None
    total_active_energy_aplus: Optional[ActiveEnergy] = None


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class Module:
    historic_vars: HistoricVars
    model: str
    user_attributes: Dict[str, Any]
    house_id: str
    last_communication: int
    module_id: str
    hardware_attributes: Dict[str, Any]
    creation_date: str
    state_vars: StateVars
    name: str
    vendor: str
    connectivity_state: str
    firmware_version: str
    groups: List[str]
    device_id: str
    module_local_id: str
    favorite: bool
    legacy_module_local_id: str
    serial_number: str


# @dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
# @dataclass
# class EnergyValue:
#     real_value: float
#     prediction_value: float

# @dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
# @dataclass
# class EnergyCost:
#     real_cost: float
#     prediction_cost: float

# @dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
# @dataclass
# class Prediction:
#     date: field(metadata=config(decoder=date_from_string_day))
#     value: EnergyValue
#     cost: EnergyCost

# @dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
# @dataclass
# class EnergyChart:
#     start: datetime = field(
#         metadata=config(decoder=date_from_string)
#     )
#     end_billing_date: datetime = field(
#         metadata=config(decoder=date_from_string)
#     )
#     billing_period: str
#     prediction_chart: List[Prediction]
