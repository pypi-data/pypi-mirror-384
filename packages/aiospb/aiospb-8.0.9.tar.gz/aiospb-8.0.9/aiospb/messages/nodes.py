import copy
import logging
import math
from dataclasses import dataclass
from typing import AsyncGenerator

from aiospb.shared import Clock, DataType, DeviceKey, Metric, NodeOptions, UtcClock

from .ports import (
    MessageSession,
    MQTT5Client,
    MQTTError,
    MQTTMessage,
    PayloadEncoder,
    SessionIsBroken,
)
from .values import Event, Message, Seq

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NodeMessageSession(MessageSession):
    def __init__(
        self,
        key: DeviceKey,
        mqtt_client: MQTT5Client,
        node_encoder: PayloadEncoder,
        host_encoder: PayloadEncoder,
        opts: NodeOptions | None = None,
        clock: Clock | None = None,
    ):
        self._key = key
        self._client = mqtt_client
        self._nencoder = node_encoder
        self._hencoder = host_encoder
        self._opts = opts or NodeOptions()
        self._clock = clock or UtcClock()

        self._seq = Seq(-1)
        self._bd_metric = None
        self._devices = set()

        self._connected = False

    def with_options(self, opts: NodeOptions):
        self._opts = opts

    async def establish(self):
        val = 0
        if self._bd_metric and type(self._bd_metric.value) is int:
            val = Seq(self._bd_metric.value).next().value
        ts = self._clock.timestamp()
        bd_metric = Metric(ts, val, DataType.Int64, name="bdSeq")
        msg = Message(Event.NODE_HAS_DIED, self._key, sending_ts=ts)

        logger.debug("Connecting to MQTT Broker....")
        await self._client.connect(
            will=MQTTMessage(
                msg.get_topic(),
                self._nencoder.encode(msg.get_payload(bd_metric=bd_metric)),
                1,
                False,
            )
        )

        # Subscribe to host messages and command messages
        logger.debug("Subscribing to host messages....")
        await self._client.subscribe("spBv1.0/STATE/+", qos=1)
        await self._client.subscribe(
            f"spBv1.0/{self._key.group}/NCMD/{self._key.node_name}", qos=1
        )
        await self._client.subscribe(
            f"spBv1.0/{self._key.group}/DCMD/{self._key.node_name}/+", qos=1
        )

        logger.info("Connected to MQTT Broker, waiting host messages...")
        self._bd_metric = bd_metric

    async def terminate(self):
        self._connected = False
        logger.debug("Terminating session ...")
        await self._client.disconnect()
        logger.info("Session is terminated")

    def is_established(self) -> bool:
        return self._client.is_connected()

    async def publish(self, msg: Message):
        if not self._client.is_connected():
            raise SessionIsBroken()

        if msg.event in (
            Event.HOST_STATE_HAS_CHANGED,
            Event.NODE_COMMAND_IS_SENT,
            Event.DEVICE_COMMAND_IS_SENT,
        ):
            raise ValueError(f"Message of type {msg.event} can not published")
        qos = 1 if msg.event == Event.NODE_HAS_DIED else 0
        seq = None if msg.event == Event.NODE_HAS_DIED else self._seq.next().value
        bd_metric = (
            self._bd_metric
            if msg.event in (Event.NODE_IS_BORN, Event.NODE_HAS_DIED)
            else None
        )
        msg.sending_ts = self._clock.timestamp()
        encoded = self._nencoder.encode(msg.get_payload(seq, bd_metric))

        if self._opts.max_payload_size and len(encoded) > self._opts.max_payload_size:
            if msg.event in (
                Event.DEVICE_DATA_HAS_CHANGED,
                Event.NODE_DATA_HAS_CHANGED,
            ):
                await self._publish_splitted(
                    msg, math.ceil(len(encoded) / self._opts.max_payload_size)
                )
                return
            else:
                raise ValueError(
                    f"Size of {msg.event} is over {self._opts.max_payload_size} bytes"
                )

        try:
            await self._client.publish(
                MQTTMessage(
                    msg.get_topic(),
                    encoded,
                    qos,
                    False,
                )
            )
            logger.info(f"Message {msg.event} has been published to broker")
        except MQTTError as e:
            logger.error(f"Message {msg.event} can not be send by MQTTError")
            logger.exception(e)
            await self._client.disconnect()
            raise SessionIsBroken()

        self._seq = self._seq.next()

    async def _publish_splitted(self, msg: Message, n_parts: int):
        m_len = len(msg.metrics)
        size = m_len // n_parts

        if size == 0:
            raise ValueError(
                f"Not possible to split {m_len} metrics into {n_parts} parts"
            )

        low = 0
        high = size
        while True:
            if high + size > m_len:
                high = m_len

            split = copy.copy(msg)
            split.metrics = split.metrics[low:high]
            await self.publish(split)

            if high == m_len:
                return

            low = high
            high = high + size

    async def subscribe(self) -> AsyncGenerator[Message, None]:
        try:
            async for msg in self._client.messages:
                try:
                    if msg.topic.startswith("spBv1.0/STATE/"):
                        payload = self._hencoder.decode(msg.payload)
                    else:
                        payload = self._nencoder.decode(msg.payload)

                    result = Message.construct(msg.topic, payload)

                    if result.event not in (
                        Event.HOST_STATE_HAS_CHANGED,
                        Event.DEVICE_COMMAND_IS_SENT,
                        Event.NODE_COMMAND_IS_SENT,
                    ):
                        logger.warning(
                            f"NodeMessageSession can not recieve {result.event} messages, it will be lost"
                        )
                        continue

                    if (
                        result.event
                        in (Event.DEVICE_COMMAND_IS_SENT, Event.NODE_COMMAND_IS_SENT)
                        and result.key.node != self._key
                    ):
                        logger.warning(
                            f'Command requested to other node "{result.key.node}, it will be lost"'
                        )
                        continue

                    yield result
                except Exception as e:
                    logger.warning(
                        "Processing message from {msg.topic}, it will be lost"
                    )
                    logger.exception(e)
        except MQTTError as e:
            logger.warning("Connection to MQTT Server is broken")
            logger.exception(e)
        except Exception as e:
            logger.error("Unexpected exception from MQTT Server")
            logger.exception(e)

        await self._client.disconnect()
        raise SessionIsBroken()
