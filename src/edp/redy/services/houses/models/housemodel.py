from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase
from dataclasses_json import Undefined


class HouseProfile(Enum):
    Consumption = 'Consumption'
    ConsumptionES = 'ConsumptionES'
    Microgeneration = 'Microgeneration'
    SelfConsumption = 'Selfconsumption'
    CommunityConsumption = 'CommunityConsumption'
    CommunityProduction = 'CommunityProduction'
    CommunitySelfConsumption = 'CommunitySelfconsumption'
    Storage = 'Storage'


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class House:
    address: str
    house_id: str
    # permission_role: PermissionRole
    permission_role: str
    name: str
    # house_profile: HouseProfile
    house_profile: str
    classification: str
    postal_code: str
    city: str
    district: str
    country: str
    timezone: str
    service_provider: str
    status: str
    electricity_local_id: Optional[str]
    gas_local_id: Optional[str]
    is_settlement_active: bool
    product_type: str
