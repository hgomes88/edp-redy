"""Houses Service module."""
from typing import List

from edp.redy.services.api import ApiService
from edp.redy.services.houses.constants import CONTRACTED_POWER_URL
from edp.redy.services.houses.constants import HOUSES_URL
from edp.redy.services.houses.constants import TARIFF_URL
from edp.redy.services.houses.models.contractedpowermodel import ContractedPower
from edp.redy.services.houses.models.housemodel import House
from edp.redy.services.houses.models.tariffmodel import Tariff


class HousesService:
    """Houses Service class."""

    def __init__(self, api_service: ApiService) -> None:
        """Initialize the Houses Service object."""
        self._api_service = api_service

    async def get_houses(self) -> List[House]:
        """Get all houses."""
        houses_list = (await self._api_service.get(HOUSES_URL))["houses"]
        houses = House.schema().load(houses_list, many=True)
        return houses

    async def get_house_tariff(self, house_id: str) -> Tariff:
        """Get tariff linked to a house."""
        tariff_dict = await self._api_service.get(TARIFF_URL.format(house_id=house_id))
        return Tariff.from_dict(tariff_dict)

    async def get_house_contracted_power(self, house_id: str):
        """Get house contracted power info."""
        contract_dict = await self._api_service.get(
            CONTRACTED_POWER_URL.format(house_id=house_id)
        )
        return ContractedPower.from_dict(contract_dict)
