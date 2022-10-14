from typing import Any

from edp.redy.services.api import ApiService
from edp.redy.services.energy.constants import POWER_TOTALS_URL
from edp.redy.services.energy.constants import POWER_URL
from edp.redy.services.energy.constants import PREDICTION_GRAPH_URL
from edp.redy.services.energy.constants import PREDICTION_TOTAL_URL
from edp.redy.services.energy.models.predictionmodel import PredictionGraph
from edp.redy.services.energy.models.predictionmodel import PredictionTotal


class EnergyService:

    def __init__(self, api_service: ApiService) -> None:
        self._api_service = api_service

    async def get_prediction_total(self, house_id: str) -> PredictionTotal:
        prediction = await self._api_service.get(
            PREDICTION_TOTAL_URL.format(house_id=house_id)
        )
        return PredictionTotal.from_dict(prediction)

    async def get_prediction_graph(self, house_id: str) -> Any:
        prediction = await self._api_service.get(
            PREDICTION_GRAPH_URL.format(house_id=house_id)
        )
        return PredictionGraph.from_dict(prediction)

    async def get_power_metering(
        self,
        house_id: str,
        resolution: str,
        start: str,
        end: str
    ) -> Any:
        return await self._api_service.get(
            POWER_URL.format(house_id=house_id),
            params={'end': end, 'start': start, 'resolution': resolution}
        )

    async def get_totals(self, house_id: str) -> Any:
        return await self._api_service.get(
            POWER_TOTALS_URL.format(house_id=house_id)
        )
