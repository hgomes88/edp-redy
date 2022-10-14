from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Optional

from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class StateVariable:
    action: Optional[Dict[str, Any]]
    platform_name: str
    realtime: bool
    hardware_name: str
