from dataclasses import dataclass
from enum import Enum

from aiospb.messages.values import Message

from ..shared import DataType, DeviceKey, Metric, ValueType


@dataclass
class MinMetricInfo:
    """Minimal metric information for sending a compressed metric"""

    data_type: DataType
    alias: int = 0


@dataclass(frozen=True)
class WriteRequest:
    value: ValueType
    metric_name: str = ""
    alias: int = 0

    def construct_compresed_metric(self, timestamp: int, info: MinMetricInfo) -> Metric:
        """Construct a metric, avoiding name if alias exist"""
        return Metric(
            timestamp,
            self.value,
            info.data_type,
            info.alias,
            self.metric_name if info.alias == 0 else "",
        )


class WritingResolution(Enum):
    BadWriting = 0
    EdgeIsOffline = 5
    HostIsOffline = 10
    MetricNotFound = 15
    Cancelled = 20
    GoodWriting = 192
    StaleWriting = 500
    WritingTimeout = 505


@dataclass
class CommandResponse:
    timestamp: int
    resolutions: list[WritingResolution]


@dataclass
class CommandRequest:
    key: DeviceKey
    requests: list[WriteRequest]
    writing_timeout: float = 60.0

    def resolution(self, msg: Message) -> CommandResponse | None:
        """Return results of the command, None if the message is not related to the command"""
        if msg.key != self.key:
            return
        if len(msg.metrics) != len(self.requests):
            return

        for metric, req in zip(msg.metrics, self.requests):
            if metric.alias != req.alias:
                return

            if metric.name != req.metric_name:
                return

            if metric.value != req.value:
                return

            metric.quality
