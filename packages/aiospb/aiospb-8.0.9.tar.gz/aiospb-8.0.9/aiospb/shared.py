import abc
import asyncio
import datetime
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Self, TypeAlias


class SparkplugBError(Exception):
    """A Sparkplug B norm is broken"""


class Clock(abc.ABC):
    # @abc.abstractmethod
    # def now(self) -> int:
    #     """Return current timestamp in ms"""

    # @abc.abstractmethod
    # def sleep(self, seconds: float):
    #     """Syncronous sleep for several seconds"""

    # @abc.abstractmethod
    # async def asleep(self, milliseconds: int):
    #     """Asyncronous sleep for several seconds"""

    @abc.abstractmethod
    def timestamp(self) -> int:
        """Return current timestamp in ms"""

    @abc.abstractmethod
    def get_ticker(self, interval_ms: int) -> AsyncIterator[int]:
        """Raise every interval"""

    @abc.abstractmethod
    async def wait_for(self, task: asyncio.Task, timeout_ms: int):
        """Wait for finish a task for timeout seconds, otherwise raises TimeoutError"""


class UtcClock(Clock):
    class Ticker:
        def __init__(self, interval_ms: int, clock: Clock):
            self._next_ts = ((clock.timestamp() // interval_ms) + 1) * interval_ms
            self._clock = clock
            self._interval = interval_ms

        def __aiter__(self):
            return self

        async def __anext__(self):
            wait = (self._next_ts - self._clock.timestamp()) / 1000
            if wait <= 0:
                return self._clock.timestamp()
            await asyncio.sleep(wait)
            self._next_ts += self._interval
            return self._clock.timestamp()

    def __str__(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def sleep(self, milli_seconds: int):
        time.sleep(milli_seconds / 1000)

    async def asleep(self, mili_seconds: int):
        await asyncio.sleep(mili_seconds / 1000)

    def timestamp(self) -> int:
        return int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)

    async def wait(
        self, tasks: list[asyncio.Task], timeout: float | None = None
    ) -> tuple[set[asyncio.Task], set[asyncio.Task]]:
        return await asyncio.wait(tasks, timeout=timeout)

    async def wait_for(self, task: asyncio.Task, timeout_ms: int):
        return await asyncio.wait_for(task, timeout=timeout_ms / 1000)

    def get_ticker(self, interval_ms: int) -> AsyncIterator[int]:
        return self.Ticker(interval_ms, self)


@dataclass
class DeviceKey:
    path: str

    def __post_init__(self):
        if self.path.count("/") > 2:
            raise ValueError(
                f"Path {self.path} has too much levels to be a device/host"
            )

    @property
    def node(self) -> Self | None:
        match self.path.count("/"):
            case 1:
                return self
            case 2:
                tokens = self.path.split("/")
                return self.__class__("/".join(tokens[:2]))

    @property
    def hostname(self) -> str:
        if self.path.count("/") == 0:
            return self.path
        return ""

    @property
    def group(self) -> str:
        if self.path.count("/"):
            return self.path[: self.path.find("/")]
        return ""

    @property
    def node_name(self) -> str:
        tokens = self.path.split("/")
        if len(tokens) > 1:
            return tokens[1]
        return ""

    @property
    def device_name(self) -> str:
        tokens = self.path.split("/")
        if len(tokens) == 3:
            return tokens[2]
        return ""

    def __str___(self):
        return self.path

    def __hash__(self):
        return hash(self.path)


class MessageType(Enum):
    NBIRTH = "NBIRTH"
    NDATA = "NDATA"
    NDEATH = "NDEATH"
    NCMD = "NCMD"
    DBIRTH = "DBIRTH"
    DDATA = "DDATA"
    DDEATH = "DDEATH"
    DCMD = "DCMD"
    STATE = "STATE"

    def is_node_message(self) -> bool:
        return self in (
            MessageType.NBIRTH,
            MessageType.NDATA,
            MessageType.NDEATH,
            MessageType.NCMD,
        )

    def is_device_message(self) -> bool:
        return self in (
            MessageType.DBIRTH,
            MessageType.DDATA,
            MessageType.DDEATH,
            MessageType.DCMD,
        )

    def is_host_message(self) -> bool:
        return self == MessageType.STATE


class Quality(Enum):
    BAD = 0
    GOOD = 192
    STALE = 500


ValueType: TypeAlias = bool | int | float | str | bytes | None


class DataType(Enum):
    Unknown = 0
    Int8 = 1
    Int16 = 2
    Int32 = 3
    Int64 = 4
    UInt8 = 5
    UInt16 = 6
    UInt32 = 7
    UInt64 = 8
    Float = 9
    Double = 10
    Boolean = 11
    String = 12
    DateTime = 13
    Text = 14
    UUID = 15
    DataSet = 16
    Bytes = 17
    File = 18
    Template = 19
    PropertySet = 20
    PropertySetList = 21
    Int8Array = 22
    Int16Array = 23
    Int32Array = 24
    Int64Array = 2
    UInt8Array = 26
    UInt16Array = 27
    UInt32Array = 28
    UInt64Array = 29
    FloatArray = 30
    DoubleArray = 31
    BooleanArray = 32
    StringArray = 33
    DateTimeArray = 34

    @classmethod
    def for_(cls, value: ValueType) -> Self:
        v_type = type(value)
        if v_type not in _DEFAULT_DTs:
            raise ValueError(f"There is no default for type {v_type}")
        return _DEFAULT_DTs[v_type]

    def convert_value(self, str_value: str) -> ValueType:
        if str_value == "None":
            return

        if "Int" in self.name:
            return int(float(str_value))

        if "Float" in self.name or "Double" in self.name:
            return float(str_value)

        if "Boolean" == self.name:
            return str_value and str_value.lower() != "false"

        if "Bytes" == self.name:
            return str_value.encode()

        return str_value


_DEFAULT_DTs = {
    int: DataType.Int64,
    float: DataType.Float,
    bool: DataType.Boolean,
    str: DataType.String,
    bytes: DataType.Bytes,
}


@dataclass(frozen=True)
class PropertyValue:
    value: ValueType
    data_type: DataType

    def to_dict(self) -> dict[str, ValueType]:
        return {"value": self.value, "dataType": self.data_type.name}

    @classmethod
    def from_dict(cls, dump: dict[str, Any]) -> Self:
        datatype = (
            DataType[dump["dataType"]]
            if type(dump["dataType"]) is str
            else DataType(dump["dataType"])
        )
        return cls(dump["value"], datatype)

    @classmethod
    def from_value(cls, value: ValueType) -> Self:
        value_type = type(value)
        if value_type not in _DEFAULT_DTs:
            raise ValueError(f"Not default for type {type(value)}")

        datatype = _DEFAULT_DTs[value_type]

        return cls(value, datatype)


# @dataclass(frozen=True)
# class PropertySet:
#     """Map or properties"""

#     keys: tuple[str, ...] = field(default_factory=tuple)
#     values: tuple[PropertyValue, ...] = field(default_factory=tuple)

#     def __contains__(self, key: str) -> bool:
#         return key in self.keys

#     def __getitem__(self, key: str) -> PropertyValue:
#         try:
#             index = self.keys.index(key)
#         except ValueError:
#             raise KeyError(f"Key {key} not found in properties")

#         return self.values[index]

#     def __bool__(self) -> bool:
#         return bool(self.keys)

#     def get(self, key: str, default: ValueType) -> ValueType:
#         try:
#             keys = [key.lower() for key in self.keys]
#             index = keys.index(key.lower())
#         except ValueError:
#             return default
#         return self.values[index].value

#     @classmethod
#     def from_dict(cls, dump: dict[str, Any]) -> Self:
#         """Construct a property set from a dict"""
#         keys = tuple(sorted(dump.keys()))
#         return cls(keys, tuple([PropertyValue.from_dict(dump[key]) for key in keys]))

#     @classmethod
#     def from_kwargs(cls, **kwargs) -> Self:
#         """Construct property set from keywords arguments"""
#         keys = tuple(sorted(kwargs.keys()))

#         return cls(keys, tuple([kwargs[key] for key in keys]))

#     def as_dict(self) -> dict[str, dict[str, Any]]:
#         """Convert object to a dict"""
#         return {key: value.to_dict() for key, value in zip(self.keys, self.values)}


def _to_snake_case(input_string):
    """
    Convert any naming convention to snake_case.
    Handles camelCase, PascalCase, kebab-case, space-separated, and mixed formats.
    """
    if not input_string:
        return input_string

    # Replace special characters (except alphanumeric and spaces) with spaces
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", input_string)

    # Convert camelCase/PascalCase by adding spaces before uppercase letters
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)

    # Convert to lowercase and replace multiple spaces with a single space
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)

    # Replace spaces with underscores
    s = s.replace(" ", "_")

    # Handle multiple underscores
    s = re.sub(r"_+", "_", s)

    # Remove leading/trailing underscores
    s = s.strip("_")

    return s


class PropertySet(dict):
    """
    A dictionary subclass that converts keys to snake_case before storing
    and allows searching with any key notation.
    """

    def __setitem__(self, key, value):
        """Store the item with the key converted to snake_case."""
        if type(value) is not PropertyValue:
            raise ValueError(f"Value shall be PropertyValue, not {type(value)}")

        snake_key = _to_snake_case(key)
        super().__setitem__(snake_key, value)

    def __getitem__(self, key):
        """Retrieve an item using any key notation."""
        snake_key = _to_snake_case(key)
        return super().__getitem__(snake_key)

    def __delitem__(self, key):
        """Delete an item using any key notation."""
        snake_key = _to_snake_case(key)
        super().__delitem__(snake_key)

    def __contains__(self, key):
        """Check if a key (in any notation) exists."""
        snake_key = _to_snake_case(key)
        return super().__contains__(snake_key)

    def get(self, key, default=None):
        """Get an item with any key notation, with optional default."""
        snake_key = _to_snake_case(key)
        return super().get(snake_key, default)

    def setdefault(self, key, default=None):
        """Set default value for a key in any notation."""
        snake_key = _to_snake_case(key)
        return super().setdefault(snake_key, default)

    def pop(self, key, *args):
        """Pop an item using any key notation."""
        snake_key = _to_snake_case(key)
        return super().pop(snake_key, *args)

    def update(self, *args, **kwargs):
        """Update the dictionary with key-value pairs, converting keys to snake_case."""
        if args:
            other = args[0]
            if isinstance(other, dict):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value


@dataclass
class Metric:
    """Data Transfer Object (dto) to be included in Sparkplug Messages"""

    timestamp: int
    value: ValueType
    data_type: DataType
    alias: int = 0
    name: str = ""
    properties: PropertySet = field(default_factory=PropertySet)
    is_transient: bool = False
    is_historical: bool = False

    @classmethod
    def from_dict(cls, dump: dict[str, Any]) -> Self:
        """Construct dto from a dict"""
        return cls(
            dump["timestamp"],
            dump["value"],
            DataType[dump["dataType"]],
            dump.get("alias", 0),
            dump.get("name", ""),
            PropertySet(
                {
                    key: PropertyValue.from_dict(value)
                    for key, value in dump.get("properties", {}).items()
                }
            ),
            dump.get("is_transient", False),
            dump.get("is_historical", False),
        )

    def as_dict(self) -> dict[str, Any]:
        """Convert dto to dict for parsing"""
        dump = {
            "timestamp": self.timestamp,
            "value": self.value,
            "dataType": self.data_type.name,
        }
        if self.alias:
            dump["alias"] = self.alias

        if self.name:
            dump["name"] = self.name

        if self.is_transient:
            dump["is_transient"] = True

        if self.properties:
            dump["properties"] = {
                key: value.as_dict() for key, value in self.properties
            }

        if self.is_historical:
            dump["is_historical"] = True
        return dump

    @property
    def quality(self) -> Quality | None:
        if not self.properties or "quality" not in self.properties:
            return

        return Quality(self.properties["quality"].value)

    @quality.setter
    def quality(self, q: Quality):
        self.properties["quality"] = PropertyValue(q.value, DataType.Int32)


@dataclass
class HostOptions:
    group: str = "+"
    reorder_time: float = 2.0  # in s
    notify_timeout: float = 10.0  # in s

    def apply(self, session):
        session._opts = self


@dataclass
class NodeOptions:
    historian_dir: str = (
        ""  # default is InMemHistorian. Set directory path to be FSHistorian
    )
    primary: str = ""
    scan_rate: int = 60000  # in ms, default is 1 min
    write_timeout: float = 10.0  # units in s
    reorder_time: float = 2.0  # units in s
    max_payload_size: int = 0  # units are bytes, default 0, no split payload

    def apply(self, session):
        session._opts = self
