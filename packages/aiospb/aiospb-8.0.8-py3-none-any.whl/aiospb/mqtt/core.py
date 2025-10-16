import abc
import base64
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Any, Self

from ..data import Metric


def matches_topic(pattern: str, value: str) -> bool:
    """
    Recursively checks if a topic matches a pattern with + and # wildcards.

    :param pattern: The pattern to match against (e.g., "home/+/temperature").
    :param value: The topic to check (e.g., "home/livingroom/temperature").
    :return: True if the topic matches the pattern, False otherwise.
    """
    # Split the topic and pattern into parts based on '/'
    topic_parts = value.split("/")
    pattern_parts = pattern.split("/")

    # Base case: if both topic and pattern are empty, they match
    if not topic_parts and not pattern_parts:
        return True

    # If one is empty and the other is not, they don't match
    if not topic_parts or not pattern_parts:
        return False

    # Get the current level of the topic and pattern
    current_topic = topic_parts[0]
    current_pattern = pattern_parts[0]

    # If the current pattern is '#', it matches the rest of the topic
    if current_pattern == "#":
        return True

    # If the current topic match
    if current_pattern == "+" or current_pattern == current_topic:
        return matches_topic("/".join(pattern_parts[1:]), "/".join(topic_parts[1:]))

    try:
        if re.fullmatch(current_pattern, current_topic):
            return matches_topic("/".join(pattern_parts[1:]), "/".join(topic_parts[1:]))
    except re.error:
        # If the pattern is not a valid regex, treat it as a literal string
        if current_pattern == current_topic:
            return matches_topic("/".join(pattern_parts[1:]), "/".join(topic_parts[1:]))

    # If none of the above, they don't match
    return False


@dataclass
class Topic:
    value: str

    @property
    def component_name(self) -> str:
        items = self.value.split("/")
        if items[1] == "STATE":
            return "/".join(items[2:])
        else:
            return "/".join([items[1]] + items[3:])

    @property
    def message_type(self) -> str:
        items = self.value.split("/")
        if items[1] == "STATE":
            return "STATE"
        return items[2]

    @classmethod
    def from_component(cls, name: str, message_type: str) -> Self:
        if message_type not in (
            "STATE",
            "NDATA",
            "NBIRTH",
            "NDEATH",
            "NCMD",
            "DDATA",
            "DBIRTH",
            "DDEATH",
        ):
            raise ValueError(f'Message type "{message_type}" is not a standard')
        if message_type == "STATE":
            return cls(f"spBv1.0/STATE/{name}")
        items = name.split("/")
        return cls(f"spBv1.0/{items[0]}/{message_type}/{'/'.join(items[1:])}")


@dataclass
class Payload(abc.ABC):
    timestamp: int

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, payload_map: dict[str, Any]) -> Self:
        """Create a payload from a plain dict"""

    @abc.abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for parsing"""


class MessageType(Enum):
    STATE = "STATE"
    NBIRTH = "NBIRTH"
    NDATA = "NDATA"
    NDEATH = "NDEATH"
    NCMD = "NCMD"
    DBIRTH = "DBIRTH"
    DDATA = "DDATA"
    DDEATH = "DDEATH"
    DCMD = "DCMD"


class ComponentType:
    HOST = "HOST"
    SP_DEVICE = "SP_DEVICE"
    EDGE_NODE = "EDGE_NODE"


@dataclass
class SpbMessage:
    component_name: str
    message_type: MessageType
    payload: Payload

    def __pos_init__(self):
        ...

    @property
    def topic(self) -> str:
        """Message type"""
        items = self.component_name.split("/")
        if len(items) == 1:
            return f"spBv1.0/STATE/{items[0]}"
        elif len(items) == 2:
            return f"spBv1.0/{items[0]}/{self.message_type}/{items[1]}"
        elif len(items) == 3:
            return f"spBv1.0/{items[0]}/{self.message_type}/{items[1]}/{items[3]}"

        raise ValueError(f"Component name {self.component_name} has level over 3")

    @property
    def component_type(self) -> ComponentType:
        return {
            0: ComponentType.HOST,
            1: ComponentType.EDGE_NODE,
            2: ComponentType.SP_DEVICE,
        }[self.component_name.count("/")]


@dataclass
class Will:
    """Will message to sent to MQTT broker"""

    message: SpbMessage
    qos: int
    retain: bool


class MqttClient(abc.ABC):
    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Is the client connected to the Broker?"""

    @abc.abstractmethod
    async def connect(self, component_name: str, will: Will):
        """Connect a component to MQTT server"""

    @abc.abstractmethod
    async def publish(self, message: SpbMessage, qos: int, retain: bool):
        """Publish a message  to the topic"""

    @abc.abstractmethod
    async def deliver_message(self) -> SpbMessage:
        """Return a messsage recieved from the MQTT Server"""

    @abc.abstractmethod
    async def subscribe(self, topic: str, qos: int):
        """Subscribe the component to recieve messages from a topic"""

    @abc.abstractmethod
    async def disconnect(self):
        """Disconnect the client from the MQTT server"""


@dataclass
class HostPayload(Payload):
    """Payload to send by MQTT for State messages"""

    online: bool

    @classmethod
    def from_dict(cls, payload_map: dict[str, Any]) -> Self:
        """Create a payload from a plain dict"""
        return cls(payload_map["timestamp"], payload_map["online"])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for parsing"""
        return {"timestamp": self.timestamp, "online": self.online}


@dataclass
class MessageContent(abc.ABC):
    """Interface of a message content"""

    @abc.abstractmethod
    async def send(
        self,
        mqtt_client: "MqttClient",
        timestamp: int,
        component_name: str,
        seq: int | None = None,
    ):
        """Publish to MQTT Broker the content of the message"""


@dataclass
class NodePayload(Payload):
    """Payload to send by MQTT for/to edge node messages"""

    metrics: list[Metric]
    seq: int | None = None

    @classmethod
    def from_dict(cls, payload_map: dict[str, Any]) -> Self:
        """Create a payload from a plain dict"""
        return cls(
            payload_map["timestamp"],
            [Metric.from_dict(value) for value in payload_map["metrics"]],
            payload_map.get("seq"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for parsing"""
        outcome = {
            "timestamp": self.timestamp,
            "metrics": [dto.as_dict() for dto in self.metrics],
        }
        if self.seq is not None:
            outcome["seq"] = self.seq

        return outcome


@dataclass
class MqttConfig:
    hostname: str
    port: int
    credentials: str = ""
    ca_cert: str = ""
    keepalive: int = 30

    def __post_init__(self):
        self.port = int(self.port)

    def deploy_certificate_file(self) -> str:
        """Save a certificate content to a file and return its filename"""
        if not self.ca_cert:
            raise ValueError("There is no certificate to save")

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            content = "-----BEGIN CERTIFICATE-----\n"
            for line in range(500):
                if (line + 1) * 64 > len(self.ca_cert):
                    content += self.ca_cert[line * 64 :] + "\n"
                    break

                content += self.ca_cert[line * 64 : (line + 1) * 64] + "\n"

            content += "-----END CERTIFICATE-----"
            f.write(content)
            return f.name

    def login_info(self) -> tuple[str | None, str | None]:
        """Return username and password for login to the MQTT Server"""

        if not self.credentials:
            return (None, None)

        tokens = (base64.b64decode(self.credentials).decode()).split(":")
        return (tokens[0], ":".join(tokens[1:]))


class MessageEncoder(abc.ABC):
    """Encode the message before sending it as payload in the message"""

    @abc.abstractmethod
    def encode(self, payload: Payload) -> bytes:
        """Convert a message to a payload"""

    @abc.abstractmethod
    def decode(self, payload: bytes) -> Payload:
        """Convert payload to a message object"""


class MqttError(Exception):
    """Wraps error of comunications by any MQTT adapter"""
