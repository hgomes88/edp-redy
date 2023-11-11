"""State variables service module."""
from typing import List

from edp.redy.services.api import ApiService
from edp.redy.services.statevars.constants import STATE_VARS_URL
from edp.redy.services.statevars.models.statevarsmodel import StateVariable


class StateVariablesService:
    """State variables service class."""

    def __init__(self, api_service: ApiService) -> None:
        """Init State Variables service."""
        self._api_service = api_service

    async def get_state_variables(self) -> List[StateVariable]:
        """Get state variables."""
        state_vars_list = (await self._api_service.get(STATE_VARS_URL))[
            "moduleStateVariables"
        ]
        state_vars = StateVariable.schema().load(state_vars_list, many=True)
        return state_vars
