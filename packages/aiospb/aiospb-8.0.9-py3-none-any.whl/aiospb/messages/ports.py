import abc
from typing import AsyncIterable, AsyncIterator

from .values import DeviceKey, Event, Message, MQTTMessage, Payload


class SessionIsBroken(Exception):
    """MessageSession has broken accidentallly"""


class MessageSession(abc.ABC):
    """Interface to manage messages, plain msgs are the only value objects it manages"""

    @abc.abstractmethod
    async def establish(self):
        ...

    @abc.abstractmethod
    async def terminate(self):
        ...

    @abc.abstractmethod
    def is_established(self) -> bool:
        ...

    @abc.abstractmethod
    async def subscribe(self) -> AsyncIterable[Message]:
        yield Message(Event.NODE_HAS_DIED, DeviceKey(""))

    @abc.abstractmethod
    async def publish(self, msg: Message):
        ...


class MQTTError(Exception):
    """Connection error to MQTT Broker, it implies clien is not connected"""

    def __init__(self, wrapped: Exception):
        self.wrapped = wrapped
        super().__init__(str(wrapped))


class MQTT5Client(abc.ABC):
    """Interface to publish messages to MQTT"""

    @abc.abstractmethod
    async def connect(self, will: MQTTMessage):
        """Connect to MQTTBroker"""

    @abc.abstractmethod
    async def publish(self, message: MQTTMessage):
        """Publish message to MQTT broker, it disconnect from broker if MQTTError"""

    @abc.abstractmethod
    async def disconnect(self):
        """Disconnect from the MQTTBroker, it shouldn't raise any exception..."""

    @abc.abstractmethod
    async def subscribe(self, wildcard: str, qos: int):
        """Subscribe to recieve MQTT broker messages, it disconnect from broker if MQTTError"""

    @abc.abstractmethod
    async def unsubscribe(self, wildcard: str):
        """Unsubscribe to recieve MQTT broker messages, it disconnect from broker if MQTTError"""

    @property
    @abc.abstractmethod
    def messages(self) -> AsyncIterator[MQTTMessage]:
        """Messages subscribed are recevieved in a async for"""

    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Check if the client is connected to MQTT broker"""


class EncodingError(Exception):
    """Failure when encoding/decoding the payload of MQTTMessage"""


class PayloadEncoder(abc.ABC):
    """Encode the message before sending it as payload in the message"""

    @abc.abstractmethod
    def encode(self, payload: Payload) -> bytes:
        """Convert a payload to a sequence of bytes"""
        ...

    @abc.abstractmethod
    def decode(self, b: bytes) -> Payload:
        """Convert bytes to a payload class"""
