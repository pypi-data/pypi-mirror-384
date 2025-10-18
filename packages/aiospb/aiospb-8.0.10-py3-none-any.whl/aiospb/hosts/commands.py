import abc
import asyncio

from aiospb.hosts.values import (
    CommandRequest,
    CommandResponse,
    MinMetricInfo,
    WritingResolution,
)
from aiospb.messages import Event, Message
from aiospb.shared import Clock, DeviceKey, Metric, Quality, UtcClock


class MinMetricInfoCache(abc.ABC):
    """Interface to persist aliases and data_type of metrics to be constructed from WritingRequest"""

    @abc.abstractmethod
    async def get(self, key: DeviceKey, names: list[str]) -> list[MinMetricInfo]:
        ...

    @abc.abstractmethod
    async def set(self, key: DeviceKey, info: dict[str, MinMetricInfo]):
        ...

    @abc.abstractmethod
    async def remove(self, key: DeviceKey):
        ...


class MetricsCreator:
    """Create a command with compressed metrics from a CommandRequest"""

    def __init__(self, cache: MinMetricInfoCache, clock: Clock | None = None):
        self._cache = cache
        self._clock = clock or UtcClock()

    async def update_metric_pars(self, msg: Message):
        """Update the parameters cache to construct commands"""
        if msg.event in (Event.DEVICE_IS_BORN, Event.NODE_IS_BORN):
            await self._cache.set(
                msg.key,
                {m.name: MinMetricInfo(m.data_type, m.alias) for m in msg.metrics},
            )

        if msg.event in (Event.DEVICE_HAS_DIED, Event.NODE_HAS_DIED):
            await self._cache.remove(msg.key)

    async def construct_writing_metrics(self, request: CommandRequest) -> list[Metric]:
        metric_pars = await self._cache.get(
            request.key, [req.metric_name for req in request.requests]
        )
        ts = self._clock.timestamp()
        return [
            req.construct_compresed_metric(ts, pars)
            for req, pars in zip(request.requests, metric_pars)
        ]


class _CommandPipe:
    def __init__(self, metrics: list[Metric], timeout: float):
        self._metrics = metrics
        self._timeout = timeout
        self._event = asyncio.Event()
        self._resolutions = [WritingResolution.WritingTimeout] * len(metrics)

    def device_has_died(self):
        self._resolutions = [WritingResolution.EdgeIsOffline] * len(self._metrics)
        self._event.set()

    def is_executed(self, metrics: list[Metric]) -> bool:
        if len(metrics) != len(self._metrics):
            return False

        resolutions = []
        for dm, cm in zip(metrics, self._metrics):
            if dm.name and dm.name != cm.name:
                return False

            if dm.alias and dm.alias != cm.alias:
                return False

            if dm.value != cm.value:
                return False

            res = WritingResolution.GoodWriting
            match dm.quality:
                case Quality.BAD:
                    res = WritingResolution.BadWriting
                case Quality.STALE:
                    res = WritingResolution.StaleWriting

            resolutions.append(res)
        self._resolutions = resolutions
        self._event.set()
        return True

    async def finish(self) -> list[WritingResolution]:
        try:
            await asyncio.wait_for(self._event.wait(), self._timeout)
        except TimeoutError:
            pass

        return self._resolutions


class CommandFollower:
    def __init__(self, clock: Clock | None = None):
        self._clock = clock or UtcClock()

        self._pendings = {}

    async def update_command_pipes(self, msg: Message):
        if msg.event in (Event.DEVICE_IS_BORN, Event.NODE_IS_BORN):
            self._pendings[msg.key] = []

        if msg.event in (Event.DEVICE_DATA_HAS_CHANGED, Event.NODE_DATA_HAS_CHANGED):
            for p in self._pendings.get(msg.key, []):
                if p.is_executed(msg.metrics):
                    break

        if msg.event in (Event.DEVICE_HAS_DIED, Event.NODE_HAS_DIED):
            for pipe in self._pendings.pop(msg.key, []):
                pipe.device_has_died()

    async def follow_command(
        self, key: DeviceKey, metrics: list[Metric], timeout: float = 60.0
    ) -> CommandResponse:
        pipe = _CommandPipe(metrics, timeout)
        if key not in self._pendings:
            return CommandResponse(
                self._clock.timestamp(),
                [WritingResolution.EdgeIsOffline] * len(metrics),
            )

        self._pendings[key].append(pipe)

        resolutions = await pipe.finish()
        if key in self._pendings:
            self._pendings[key].remove(pipe)

        return CommandResponse(self._clock.timestamp(), resolutions)
