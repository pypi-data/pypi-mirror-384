from copy import deepcopy

from aiospb.hosts import MinMetricInfo, MinMetricInfoCache
from aiospb.nodes import (
    Historian,
    MetricInfo,
    MetricNotFound,
    MetricsNetwork,
    Reading,
    ReadingStore,
)
from aiospb.shared import DataType, DeviceKey, Metric, Quality, ValueType


class InMemHistorian(Historian):
    """Implementation of historian in memory,

    for acceptance tests purpose"""

    def __init__(self):
        self._data = {}

    async def save(self, key: DeviceKey, metrics: list[Metric]):
        if key not in self._data:
            self._data[key] = []

        metrics = deepcopy(metrics)
        for metric in metrics:
            metric.is_historical = True
        self._data[key].extend(metrics)

    async def load(self, key: DeviceKey) -> list[Metric]:
        if key not in self._data:
            return []
        return self._data[key]

    async def clear(self, key: DeviceKey):
        self._data.pop(key)

    def get_device_keys(self, node_key: DeviceKey) -> list[DeviceKey]:
        return [key for key in self._data.keys() if key.node == node_key]


class InMemReadingStore(ReadingStore):
    """Implementation in RAM memory, not valid if too much metrics"""

    def __init__(self):
        self._readings = {}
        self._aliases = {}

    async def get(self, ids: list[int | str]) -> list[Reading]:
        aliases = [id if type(id) is int else self._aliases[id] for id in ids]
        return [self._readings.get(alias, Reading.none()) for alias in aliases]

    async def set(self, readings: list[Reading]):
        for r in readings:
            if r.alias and r.alias in self._readings:
                self._readings[r.alias] = self._readings[r.alias].update(
                    r.value, r.quality
                )
                continue

            if r.metric_name and r.metric_name in self._aliases:
                alias = self._aliases[r.metric_name]
                self._readings[alias] = self._readings[alias].update(r.value, r.quality)
                continue

            # Only save readings with alias & metric_name
            if r.metric_name and r.alias:
                self._readings[r.alias] = r
                self._aliases[r.metric_name] = r.alias


class InMemMinMetricInfoCache(MinMetricInfoCache):
    """Implementation in RAM memory,

    for low quantity of connected nodes and metrics, otherwise use fs"""

    def __init__(self):
        self._data = {}

    async def get(self, key: DeviceKey, names: list[str]) -> list[MinMetricInfo]:
        if key not in self._data:
            return [MinMetricInfo(DataType.Unknown)] * len(names)

        return [
            self._data[key].get(name, MinMetricInfo(DataType.Unknown)) for name in names
        ]

    async def set(self, key: DeviceKey, info: dict[str, MinMetricInfo]):
        if key not in self._data:
            self._data[key] = {}

        self._data[key].update(info)

    async def remove(self, key: DeviceKey):
        self._data.pop(key, None)
