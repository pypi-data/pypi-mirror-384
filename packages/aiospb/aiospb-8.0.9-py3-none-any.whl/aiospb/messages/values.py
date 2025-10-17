from dataclasses import dataclass, field
from enum import Enum
from typing import Self

from ..shared import DeviceKey, Metric


@dataclass
class MQTTMessage:
    """Message managed by the MQTT server"""

    topic: str
    payload: bytes
    qos: int = 0
    retain: bool = False


@dataclass
class Seq:
    value: int = -1

    def next(self) -> "Seq":
        if self.value == 255:
            return Seq(0)

        return Seq(self.value + 1)


class Event(Enum):
    NODE_IS_BORN = 0
    DEVICE_IS_BORN = 1
    NODE_DATA_HAS_CHANGED = 2
    DEVICE_DATA_HAS_CHANGED = 3
    DEVICE_HAS_DIED = 4
    NODE_HAS_DIED = 5
    NODE_COMMAND_IS_SENT = 6
    DEVICE_COMMAND_IS_SENT = 7
    HOST_STATE_HAS_CHANGED = 10
    OUT_OF_SEQUENCE = 100

    @classmethod
    def from_message_type(cls, value: str) -> "Event":
        events = {
            "NBIRTH": Event.NODE_IS_BORN,
            "NDATA": Event.NODE_DATA_HAS_CHANGED,
            "NDEATH": Event.NODE_HAS_DIED,
            "NCMD": Event.NODE_COMMAND_IS_SENT,
            "DBIRTH": Event.DEVICE_IS_BORN,
            "DDATA": Event.DEVICE_DATA_HAS_CHANGED,
            "DDEATH": Event.DEVICE_HAS_DIED,
            "DCMD": Event.DEVICE_COMMAND_IS_SENT,
            "STATE": Event.HOST_STATE_HAS_CHANGED,
        }
        if value not in events:
            raise ValueError(f'Message type "{value}" is not a registered event')
        return events[value]

    def as_message_type(self) -> str:
        msgs = {
            Event.NODE_IS_BORN: "NBIRTH",
            Event.NODE_DATA_HAS_CHANGED: "NDATA",
            Event.NODE_HAS_DIED: "NDEATH",
            Event.NODE_COMMAND_IS_SENT: "NCMD",
            Event.DEVICE_IS_BORN: "DBIRTH",
            Event.DEVICE_DATA_HAS_CHANGED: "DDATA",
            Event.DEVICE_HAS_DIED: "DDEATH",
            Event.DEVICE_COMMAND_IS_SENT: "DCMD",
            Event.HOST_STATE_HAS_CHANGED: "STATE",
        }
        return msgs[self]


@dataclass
class Payload:
    timestamp: int
    metrics: list[Metric] = field(default_factory=list)
    seq: int | None = None
    online: bool | None = None


@dataclass
class Message:
    event: Event
    key: DeviceKey
    metrics: list[Metric] = field(
        default_factory=list
    )  # No when death certificate or HOST_STATE_HAS_CHANGED
    online: bool | None = None  # No when node/device message
    sending_ts: int = 0  # if it is 0 is because it's not yet sent

    def get_topic(self) -> str:
        if self.event in (
            Event.NODE_IS_BORN,
            Event.NODE_DATA_HAS_CHANGED,
            Event.NODE_HAS_DIED,
            Event.NODE_COMMAND_IS_SENT,
        ):
            return f"spBv1.0/{self.key.group}/{self.event.as_message_type()}/{self.key.node_name}"

        if self.event in (
            Event.DEVICE_IS_BORN,
            Event.DEVICE_DATA_HAS_CHANGED,
            Event.DEVICE_HAS_DIED,
            Event.DEVICE_COMMAND_IS_SENT,
        ):
            return f"spBv1.0/{self.key.group}/{self.event.as_message_type()}/{self.key.node_name}/{self.key.device_name}"

        if self.event == Event.HOST_STATE_HAS_CHANGED:
            return f"spBv1.0/STATE/{self.key.hostname}"

        raise NotImplementedError(f"Event {self.event} has not topic defined")

    def get_payload(self, seq: int | None = None, bd_metric: Metric | None = None):
        # Preconditions
        if bd_metric and self.event not in (Event.NODE_IS_BORN, Event.NODE_HAS_DIED):
            raise ValueError(f"Event {self.event} can not have any bd_metric")

        if seq is not None and self.event in (
            Event.HOST_STATE_HAS_CHANGED,
            Event.DEVICE_COMMAND_IS_SENT,
            Event.NODE_COMMAND_IS_SENT,
            Event.NODE_HAS_DIED,
        ):
            raise ValueError(f"Event {self.event} doesn't allow sequence value {seq}")

        return Payload(
            self.sending_ts,
            self.metrics + [bd_metric] if bd_metric else self.metrics,
            seq,
            self.online,
        )

    @staticmethod
    def _get_event_and_key(topic: str) -> tuple[Event, DeviceKey]:
        tokens = topic.split("/")
        if tokens[0] != "spBv1.0":
            raise ValueError(
                f'First level of topic "{tokens[0]}" is not Sparkplug B compliance'
            )

        if len(tokens) < 3 or len(tokens) > 5:
            raise ValueError(f'Topic "{topic}" has not correct number of levels')

        key = None
        event = None
        match len(tokens):
            case 3:
                key = DeviceKey(tokens[2])
                event = Event.from_message_type(tokens[1])
            case 4:
                key = DeviceKey("/".join([tokens[1], tokens[3]]))
                event = Event.from_message_type(tokens[2])
            case _:
                key = DeviceKey("/".join([tokens[1]] + tokens[3:]))
                event = Event.from_message_type(tokens[2])

        return (event, key)

    @classmethod
    def construct(cls, topic: str, payload: Payload) -> Self:
        event, key = cls._get_event_and_key(topic)

        metrics = payload.metrics
        if event in (Event.NODE_IS_BORN, Event.NODE_HAS_DIED):  # remove bd_metric
            metrics = metrics[:-1]

        return cls(event, key, metrics, payload.online, payload.timestamp)
