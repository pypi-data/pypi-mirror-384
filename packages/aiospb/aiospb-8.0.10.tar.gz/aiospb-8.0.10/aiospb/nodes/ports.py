import abc

from ..shared import DeviceKey, Metric, ValueType
from .values import MetricInfo, Reading


class Historian(abc.ABC):
    @abc.abstractmethod
    async def save(self, key: DeviceKey, metrics: list[Metric]):
        """Persist the metrics"""

    @abc.abstractmethod
    async def load(self, key: DeviceKey) -> list[Metric]:
        """Return the persisted metrics, but marked as is_history"""

    @abc.abstractmethod
    async def clear(self, key: DeviceKey):
        """Clear all the history of a device (beacuse it was succesfully sent)"""

    @abc.abstractmethod
    def get_device_keys(self, node_key: DeviceKey) -> list[DeviceKey]:
        """List all device_keys with stored histories related to node_key"""


class ReadingStore(abc.ABC):
    @abc.abstractmethod
    async def get(self, ids: list[int | str]) -> list[Reading]:
        """Return the values of the aliases listed"""

    @abc.abstractmethod
    async def set(self, readings: list[Reading]):
        """Set a group of readings to some aliases"""


class MetricNotFound(Exception):
    def __init__(self, name: str, alias: int):
        self.name = name
        self.alias = alias
        super().__init__(f'Metric "{name}:{alias}" not found in MetricsNetwork')


class DeviceConnectionIsBroken(Exception):
    def __init__(self, key: DeviceKey, conn_name: str = ""):
        self.device_key = key
        self.conn_name = conn_name
        super().__init__(f"Connection {conn_name} to device {key} has broken")


class MetricsNetwork(abc.ABC):
    @abc.abstractmethod
    def get_device_keys(self) -> list[DeviceKey]:
        ...

    @abc.abstractmethod
    async def get_info(self, key: DeviceKey) -> list[MetricInfo]:
        """List the metric information available for a device"""
        ...

    @abc.abstractmethod
    async def read(self, key: DeviceKey, alias: int = 0, name: str = "") -> ValueType:
        """Read the current value of a metric, defined by alias or name"""

    @abc.abstractmethod
    async def write(
        self, key: DeviceKey, value: ValueType, alias: int = 0, name: str = ""
    ) -> int:
        """Write the value on the metric defined by the alias, returns it alias as confirmation"""

    @abc.abstractmethod
    async def connect_device(self, key: DeviceKey):
        """Connect device"""

    @abc.abstractmethod
    async def disconnect_device(self, key: DeviceKey):
        """Disconnect device"""
