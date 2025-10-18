from dataclasses import dataclass, field
from typing import Self

from aiospb.shared import DataType, Metric, PropertySet, Quality, ValueType


@dataclass
class Reading:
    metric_name: str
    alias: int
    value: ValueType
    data_type: DataType = DataType.Unknown
    quality: Quality = Quality.GOOD

    def update(self, value: ValueType, quality: Quality) -> "Reading":
        value = value if quality == Quality.GOOD else self.value
        return Reading(self.metric_name, self.alias, value, self.data_type, quality)

    def create_change_metric(self, timestamp: int, newer: Self) -> Metric | None:
        reading = self.update(newer.value, newer.quality)
        if reading == self:
            return

        name = self.metric_name if not self.alias else ""
        metric = Metric(timestamp, reading.value, reading.data_type, self.alias, name)
        if reading.quality != self.quality:
            metric.quality = reading.quality

        return metric

    @classmethod
    def none(cls) -> "Reading":
        return Reading("", 0, None, DataType.Unknown, Quality.BAD)


@dataclass
class MetricInfo:
    """Stable metric data, stable during a session"""

    name: str
    data_type: DataType
    properties: PropertySet = field(default_factory=PropertySet)
    alias: int = 0
    is_transient: bool = False

    def create_birth_metric(self, timestamp: int, reading: Reading) -> Metric:
        """Create metric from the metric core"""
        metric = Metric(
            timestamp,
            reading.value,
            self.data_type,
            self.alias,
            self.name,
            self.properties,
            is_transient=self.is_transient,
        )

        if reading.quality != Quality.GOOD:
            metric.quality = reading.quality

        return metric
