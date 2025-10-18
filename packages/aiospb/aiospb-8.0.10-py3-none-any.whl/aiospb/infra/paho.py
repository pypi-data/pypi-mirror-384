import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncIterator

import aiomqtt
from aiomqtt.exceptions import MqttError as AioMqttError

from aiospb.messages import MQTT5Client, MQTTError, MQTTMessage

logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    hostname: str
    port: int
    username: str = ""
    password: str = ""
    ca_cert: str = ""
    keepalive: int = 30
    conn_timeout: float = 30.0
    trys: int = 3
    try_wait: float = 0.5


class PahoMQTTClient(MQTT5Client):
    """Implementation with Paho of MQTT5Publisher and MQTTSubscriver"""

    def __init__(self, client_id: str, config: MQTTConfig):
        self._id = client_id
        self._config = config
        self._client = None

    @property
    def keepalive(self) -> float:
        return self._config.keepalive

    async def connect(self, will: MQTTMessage | None = None):
        if self._client:
            raise MQTTError(Exception(f"PahoMQTTClient already connected"))

        will_ = None
        if will:
            will_ = aiomqtt.Will(will.topic, will.payload, will.qos, will.retain)

        tls_pars = None
        if self._config.ca_cert:
            tls_pars = aiomqtt.TLSParameters(ca_certs=self._config.ca_cert)

        client = aiomqtt.Client(
            self._config.hostname,
            self._config.port,
            identifier=self._id,
            username=self._config.username,
            password=self._config.password,
            will=will_,
            protocol=aiomqtt.ProtocolVersion.V5,
            tls_params=tls_pars,
            clean_start=True,
            keepalive=self._config.keepalive,
            timeout=self._config.conn_timeout,
        )

        try:
            await client.__aenter__()
            # await asyncio.wait_for(  # It shouldn't be necessary
            #     client.__aenter__(), timeout=self._config.conn_timeout
            # )
            self._client = client
        except AioMqttError as e:
            await self._disconnect_by_mqtt_error(e)

    async def _disconnect_by_mqtt_error(self, e: Exception):
        await self.disconnect()
        raise MQTTError(e) from e

    async def publish(self, message: MQTTMessage):
        if self._client is None:
            raise MQTTError(Exception(f"PahoMQTTClient {self._id} not connected"))

        attempts = 0
        while True:
            timeout = self._config.conn_timeout
            try:
                await self._client.publish(
                    message.topic,
                    message.payload,
                    qos=message.qos,
                    retain=message.retain,
                    timeout=timeout,
                )
                return
            except asyncio.TimeoutError:
                attempts += 1
                logger.warning(
                    f"Failure by timeout publishing to {message.topic}, attempt {attempts}"
                )
                timeout = timeout * 1.5
                if attempts == 3:
                    raise TimeoutError(
                        f"After 3 attempts not possible to publish to {message.topic}"
                    )
            except AioMqttError as e:
                await self._disconnect_by_mqtt_error(e)

    async def disconnect(self):
        if self._client is None:
            return

        try:
            await self._client.__aexit__(None, None, None)
        except AioMqttError:
            pass
        finally:
            self._client = None

    def is_connected(self):
        return self._client is not None

    async def subscribe(self, wildcard: str, qos: int):
        if self._client is None:
            raise MQTTError(Exception(f"PahoMQTTClient {self._id} is not connected"))

        try:
            await self._client.subscribe(wildcard, qos=qos)
        except AioMqttError as e:
            await self._disconnect_by_mqtt_error(e)

    async def unsubscribe(self, wildcard: str):
        if self._client is None:
            raise MQTTError(Exception(f"PahoMQTTClient {self._id} is not connected"))

        try:
            await self._client.unsubscribe(wildcard)
        except AioMqttError as e:
            await self._disconnect_by_mqtt_error(e)

    @property
    def messages(self) -> AsyncIterator[MQTTMessage]:
        class MQTTMessages:
            def __init__(
                self, msgs: aiomqtt.MessagesIterator, client: "PahoMQTTClient"
            ):
                self._msgs = msgs
                self._cli = client

            def __aiter__(self):
                self._msgs.__aiter__()
                return self

            async def __anext__(self) -> MQTTMessage:
                # trys = 0
                while True:
                    try:
                        msg = await anext(self._msgs)
                        if type(msg.payload) is not bytes:
                            raise TypeError(
                                "Expected payload to be bytes, not {type(msg.payload)}"
                            )
                        return MQTTMessage(
                            msg.topic.value, msg.payload, msg.qos, msg.retain
                        )
                    except AioMqttError as e:
                        # trys += 1
                        # logger.warning(f"AioMqttError on try {trys}")
                        logger.exception(e)
                        # if trys == self._cli._config.trys:
                        logger.error(
                            f"Disconnecting while getting messages by MQTTError"
                        )
                        await self._cli._disconnect_by_mqtt_error(e)

                        # await asyncio.sleep(self._cli._config.try_wait)

        if self._client is None:
            raise MQTTError(Exception(f"PahoMQTTClient {self._id} is not connected"))

        return MQTTMessages(self._client.messages, self)
