"""Command line interface module."""
import asyncio
import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from enum import auto
from enum import Enum
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
from typing import Protocol
from typing import Tuple

import aiocron
from edp.redy.app import App
from edp.redy.app import Energy
from edp.redy.app import EnergyType
from edp.redy.app import EnergyValues
from edp.redy.app import get_app
from edp.redy.app import Power
from edp.redy.app import ValueCost
from edp.redy.app import ValueCostDate
from edp.redy.cli.argparser import parser
from edp.redy.services.devices.models.modulesmodel import Resolution

logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s "
    "%(name)s::%(funcName)s(line %(lineno)s): %(message)s",
)

log = logging.getLogger(__name__)


class PowerDeviceDataTypes(Enum):
    """Power device dta types."""

    GRID_CONSUMED = auto()
    GRID_INJECTED = auto()
    SOLAR_PRODUCED = auto()
    SOLAR_CONSUMED = auto()
    TOTAL_CONSUMED = auto()


@dataclass
class PowerDeviceData:
    """Power device data dataclass."""

    type: PowerDeviceDataTypes
    value: float


class PowerDeviceCallback(Protocol):
    """Power device callback class."""

    async def __call__(self, data: PowerDeviceData) -> None:
        """Caller of power device callback."""
        ...


@dataclass
class _PowerDeviceInfo:
    values: List[float] = field(default_factory=list)
    callbacks: List[PowerDeviceCallback] = field(default_factory=list)


class RedyPowerDevice:
    """Redy power device class."""

    def __init__(self, power: Power) -> None:
        """Init the redy power device object."""
        self._power = power
        self._cron_spec = None
        self._real_time: bool = True

        self._data_types: Dict[PowerDeviceDataTypes, _PowerDeviceInfo] = {
            t: _PowerDeviceInfo() for t in PowerDeviceDataTypes
        }

    def subscribe(self, types: Tuple[PowerDeviceDataTypes], cb: PowerDeviceCallback):
        """Subscribe to one or more power device data types."""
        for t in types:
            self._data_types[t].callbacks.append(cb)
        return self

    async def start(self, cron_spec: str = None):
        """Start the redy power device."""
        self._init_stream_callbacks()
        self._init_cron(cron_spec)

    @classmethod
    def _average_calculate(cls, values: List[float]) -> Optional[float]:
        if len(values):
            return float(sum(values) / len(values))
        return None

    def _init_cron(self, cron_spec: str = None):
        if cron_spec:
            self._real_time = False
            self._cron = aiocron.crontab(
                cron_spec, func=self._notify_averages, start=True
            )

    def _init_stream_callbacks(self):
        self._power.grid_consumed.stream(self._grid_consumed_cb)
        self._power.solar_produced.stream(self._solar_produced_cb)
        self._power.grid_injected.stream(self._grid_injected_cb)
        self._power.solar_consumed.stream(self._solar_consumed_cb)
        self._power.total_consumed.stream(self._total_consumed_cb)

    async def _notify_average(self, type: PowerDeviceDataTypes):
        info: _PowerDeviceInfo = self._data_types[type]
        avg = self._average_calculate(info.values)
        if avg is not None:
            for cb in info.callbacks:
                await cb(PowerDeviceData(type=type, value=avg))

    async def _notify_averages(self):
        try:
            for k, v in self._data_types.items():
                await self._notify_average(k)
                v.values.clear()
        except Exception:
            log.exception("Error:")

    async def _handle_cb(self, type: PowerDeviceDataTypes, value: float):
        values = self._data_types[type].values
        if self._real_time:
            if len(values):
                values[0] = value
            else:
                values.append(value)
            await self._notify_average(type)
        else:
            values.append(value)

    async def _grid_consumed_cb(self, value: float):
        await self._handle_cb(PowerDeviceDataTypes.GRID_CONSUMED, value)

    async def _grid_injected_cb(self, value: float):
        await self._handle_cb(PowerDeviceDataTypes.GRID_INJECTED, value)

    async def _solar_produced_cb(self, value: float):
        await self._handle_cb(PowerDeviceDataTypes.SOLAR_PRODUCED, value)

    async def _solar_consumed_cb(self, value: float):
        await self._handle_cb(PowerDeviceDataTypes.SOLAR_CONSUMED, value)

    async def _total_consumed_cb(self, value: float):
        await self._handle_cb(PowerDeviceDataTypes.TOTAL_CONSUMED, value)


class EnergyDeviceDataTypes(Enum):
    """Energy device data types."""

    GRID_CONSUMED = auto()
    GRID_INJECTED = auto()
    SOLAR_PRODUCED = auto()
    SOLAR_CONSUMED = auto()
    TOTAL_CONSUMED = auto()


@dataclass
class EnergyDeviceData:
    """Energy device dataclass."""

    type: EnergyDeviceDataTypes
    value: EnergyValues


class EnergyDeviceCallback(Protocol):
    """Energy device callback protocol."""

    async def __call__(self, data: EnergyDeviceData) -> None:
        """Caller of the energy device callback."""
        ...


@dataclass
class _EnergyDeviceInfo:
    values: Optional[EnergyValues] = None
    callbacks: List[EnergyDeviceCallback] = field(default_factory=list)
    energy_type: Optional[EnergyType] = None


class RedyEnergyDevice:
    """Redy energy device class."""

    def __init__(self, energy: Energy) -> None:
        """Start the redy energy device object."""
        self._energy = energy
        # Every 5 minutes and 30 seconds
        self._cron_spec = "*/15 * * * * 30"

        self._data_types: Dict[EnergyDeviceDataTypes, _EnergyDeviceInfo] = {
            t: _EnergyDeviceInfo(energy_type=self._get_energy_type(t))
            for t in EnergyDeviceDataTypes
        }

    def subscribe(self, types: Tuple[EnergyDeviceDataTypes], cb: EnergyDeviceCallback):
        """Subscribe to one or more energy device data types."""
        for t in types:
            self._data_types[t].callbacks.append(cb)
        return self

    async def start(self, cron_spec: str = "*/15 * * * * 30"):
        """Start the redy energy device."""
        self._init_cron(cron_spec)

    def _init_cron(self, cron_spec):
        self._cron = aiocron.crontab(cron_spec, func=self._notify_energy, start=True)

    def _get_energy_type(
        self, data_type: EnergyDeviceDataTypes
    ) -> Optional[EnergyType]:
        if data_type == EnergyDeviceDataTypes.GRID_CONSUMED:
            return self._energy.consumed
        elif data_type == EnergyDeviceDataTypes.GRID_INJECTED:
            return self._energy.injected
        elif data_type == EnergyDeviceDataTypes.SOLAR_CONSUMED:
            return self._energy.self_consumed
        elif data_type == EnergyDeviceDataTypes.SOLAR_PRODUCED:
            return self._energy.produced
        else:
            return None

    def _calculate_range(self) -> Tuple[Resolution, datetime, datetime]:
        MIDNIGHT = timedelta()
        QUARTER_AFTER_MIDNIGHT = timedelta(minutes=15)
        now = datetime.now()
        now_td = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        resolution = Resolution.QuarterHour

        # If between midnight and 15 min after midnight
        if MIDNIGHT <= now_td < QUARTER_AFTER_MIDNIGHT:
            # Rewind the time by 15 minutes, leading to access the data from
            # the previous day. This is to ensure we take the data from the
            # last quarter of the day
            now = now - timedelta(minutes=15)

        # Start and end can be the same, as the Redy API only cares about the day
        start = now
        end = now
        return resolution, start, end

    async def _notify_energy(self):
        try:
            resolution, start, end = self._calculate_range()

            grid_consumed = await self._get_value(
                EnergyDeviceDataTypes.GRID_CONSUMED, resolution, start, end
            )
            grid_injected = await self._get_value(
                EnergyDeviceDataTypes.GRID_INJECTED, resolution, start, end
            )
            solar_produced = await self._get_value(
                EnergyDeviceDataTypes.SOLAR_PRODUCED, resolution, start, end
            )
            solar_consumed = await self._get_value(
                EnergyDeviceDataTypes.SOLAR_CONSUMED, resolution, start, end
            )
            total_consumed = await self._total_consumed(grid_consumed, solar_consumed)

            await self._notify(EnergyDeviceDataTypes.GRID_CONSUMED, grid_consumed)
            await self._notify(EnergyDeviceDataTypes.GRID_INJECTED, grid_injected)
            await self._notify(EnergyDeviceDataTypes.SOLAR_PRODUCED, solar_produced)
            await self._notify(EnergyDeviceDataTypes.SOLAR_CONSUMED, solar_consumed)
            await self._notify(EnergyDeviceDataTypes.TOTAL_CONSUMED, total_consumed)

        except Exception:
            log.exception("Error")

    #     # If the time is < 01:00:00 no data is returned from redy at all
    #     # So, nothing should be done

    #     # If the time is 01:00:00, the
    #     # consumed = await self._energy.consumed.today(Resolution.Hour)

    #     # Else
    #     consumed = await self._energy.consumed.today(Resolution.QuarterHour)

    async def _get_value(
        self,
        data_type: EnergyDeviceDataTypes,
        resolution: Optional[Resolution],
        start: Optional[datetime],
        end: Optional[datetime],
    ) -> Optional[EnergyValues]:
        info: _EnergyDeviceInfo = self._data_types[data_type]
        value: Optional[EnergyValues] = None
        try:
            assert info.energy_type
            value = await info.energy_type.in_dates(
                resolution=resolution, start=start, end=end
            )
        except Exception:
            log.exception("Error")
        finally:
            return value

    async def _total_consumed(
        self, grid_consumed: EnergyValues, solar_consumed: EnergyValues
    ) -> Optional[EnergyValues]:
        if not grid_consumed or not solar_consumed:
            log.warning(
                "Total couldn't be calculated: "
                f"Grid Consumed: {grid_consumed}. "
                f"Solar Consumed: {solar_consumed}"
            )
            return None

        total = ValueCost(
            value=grid_consumed.total.value + solar_consumed.total.value,
            cost=grid_consumed.total.cost + solar_consumed.total.cost,
        )

        history: List[ValueCostDate] = []
        grid_consumed_dict = {str(h.date): h for h in grid_consumed.history}
        solar_consumed_dict = {str(h.date): h for h in solar_consumed.history}

        for date in grid_consumed_dict:
            grid = grid_consumed_dict[date]
            solar = solar_consumed_dict.get(date)
            if solar:
                history.append(
                    ValueCostDate(
                        value=grid.value + solar.value,
                        cost=grid.cost + solar.cost,
                        date=datetime.fromisoformat(date),
                    )
                )
            else:
                history.append(grid_consumed_dict[date])

        energy_values = EnergyValues(history=history, total=total)

        return energy_values

    async def _notify(
        self, data_type: EnergyDeviceDataTypes, value: Optional[EnergyValues] = None
    ):
        info: _EnergyDeviceInfo = self._data_types[data_type]

        if value and info.callbacks:
            for cb in info.callbacks:
                await cb(EnergyDeviceData(type=data_type, value=value))


@dataclass
class Value:
    """Value dataclass."""

    recorded_date: datetime
    recorded_total: float
    value: float


class RedyDevice:
    """Redy device class."""

    def __init__(self, app: App) -> None:
        """Initialize the redy device object."""
        self._app = app
        self._power_device = RedyPowerDevice(self._app.power)
        self._energy_device = RedyEnergyDevice(self._app.energy)

        self._data: Dict[EnergyDeviceDataTypes, Optional[Value]] = {
            t: None for t in EnergyDeviceDataTypes
        }

    @property
    def power_device(self):
        """Return the power device object."""
        return self._power_device

    @property
    def energy_device(self):
        """Return the energy device object."""
        return self._energy_device

    async def start(self):
        """Start the redy device."""
        if not self._app.started:
            await self._app.start()

        self._power_device.subscribe(
            (
                PowerDeviceDataTypes.GRID_CONSUMED,
                PowerDeviceDataTypes.GRID_INJECTED,
                PowerDeviceDataTypes.SOLAR_CONSUMED,
                PowerDeviceDataTypes.SOLAR_PRODUCED,
                PowerDeviceDataTypes.TOTAL_CONSUMED,
            ),
            self._power_cb,
        )
        # await self._power_device.start(cron_spec='01,16,31,46 * * * *')
        await self._power_device.start(cron_spec="*/15 * * * * 30")

        self._energy_device.subscribe(
            (
                EnergyDeviceDataTypes.GRID_CONSUMED,
                EnergyDeviceDataTypes.GRID_INJECTED,
                EnergyDeviceDataTypes.SOLAR_CONSUMED,
                EnergyDeviceDataTypes.SOLAR_PRODUCED,
                EnergyDeviceDataTypes.TOTAL_CONSUMED,
            ),
            self._energy_cb,
        )

        await self._energy_device.start("*/5 * * * *")

    async def _power_cb(self, app_type: PowerDeviceData):
        log.info(app_type)

    def _hourly_update(self, data: EnergyDeviceData):
        now = datetime.now()
        type = data.type
        value = data.value.total.value

        # Create object if it doesn't exist
        if self._data[type] is None:
            self._data[type] = Value(recorded_date=now, recorded_total=value, value=0)
        else:
            v = self._data[type]
            # If still in the same hour
            assert v
            if v.recorded_date.hour == now.hour:
                v.value = value - v.recorded_total
            else:
                v.value = 0
            v.recorded_date = now
            v.recorded_total = value

        if self._data[type]:
            _v: Value = cast(Value, self._data[type])
            return _v.value
        else:
            return None

    async def _energy_cb(self, data: EnergyDeviceData):
        """Energy callback."""
        log.info(f"TOTAL {data.type.name}: {data.value.total}")
        log.info(f"LAST {data.type.name}: {data.value.history[-1]}")
        log.info(f"Hourly {data.type.name}: {self._hourly_update(data)}")


async def _main():
    # Get the inputs
    args = parser.parse_args()

    # Start the app
    app = await get_app(
        username=args.username,
        password=args.password,
        user_pool_id=args.user_pool_id,
        client_id=args.client_id,
        region=args.region,
        identity_pool_id=args.identity_id,
        identity_login=args.identity_login,
    )
    await app.start()

    redy_device: RedyDevice = RedyDevice(app)

    await redy_device.start()


def main():
    """Start the main function."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main())
    loop.run_forever()


if __name__ == "__main__":
    main()
