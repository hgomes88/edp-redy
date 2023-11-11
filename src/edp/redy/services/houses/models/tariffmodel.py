"""Tariff model module."""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CostRate:
    """Cost rate dataclass."""

    ENS: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Energy:
    """Energy dataclass."""

    cost_rate: CostRate


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Power:
    """Power dataclass."""

    contracted: float
    cost_rate: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ElectricityTariff:
    """Electricity tariff dataclass."""

    energy: Energy
    power: Power
    geography: str
    hourOption: str
    type: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Tariff:
    """Tariff dataclass."""

    electricity: Optional[ElectricityTariff]
