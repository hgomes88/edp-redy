from dataclasses import dataclass

from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ContractedPower:
    contracted_power: float
    unit: str
