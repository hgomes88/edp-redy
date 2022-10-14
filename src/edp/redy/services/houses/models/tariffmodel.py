from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CostRate:
    ENS: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Energy:
    cost_rate: CostRate


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Power:
    contracted: float
    cost_rate: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ElectricityTariff:
    energy: Energy
    power: Power
    geography: str
    hourOption: str
    type: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Tariff:
    electricity: Optional[ElectricityTariff]
