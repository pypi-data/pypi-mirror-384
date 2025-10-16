import asyncio
import logging
from typing import AsyncIterable

from aiospb.messages.ports import (
    MessageSession,
    MQTT5Client,
    MQTTError,
    MQTTMessage,
    PayloadEncoder,
    SessionIsBroken,
)
from aiospb.shared import Clock, DataType, HostOptions, Metric, UtcClock

from .values import DeviceKey, Event, Message, Seq

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class _Sorter:
    def __init__(
        self,
        node_key: DeviceKey,
        output: asyncio.Queue,
        reorder_time: float = 2.0,
    ):
        self._node_key = node_key
        self._output = output
        self._time = reorder_time

        self._seq = None
        self._bd_seq = None
        self._pending = {}
        self._oos_task = None

    async def _raise_out_of_sequence(self, ts: int, seq: int, bd_seq: int):
        await asyncio.sleep(self._time)
        ts += int(self._time * 1000)
        self._output.put_nowait(
            Message(
                Event.OUT_OF_SEQUENCE,
                self._node_key,
                [
                    Metric(ts, seq, DataType.Int64, name="seq"),
                    Metric(ts, bd_seq, DataType.Int16, name="bdSeq"),
                ],
            )
        )
        self._oos_task = None

    def push_pack(self, msg: Message, seq: int | None, bd_metric: Metric | None):
        if msg.event == Event.NODE_HAS_DIED and bd_metric:
            if self._bd_seq is None or self._bd_seq != bd_metric.value:
                should = self._bd_seq.value if self._bd_seq else None
                logger.warning(
                    f'Lost of node death at "{msg.key}", should be {should} but is {bd_metric.value}'
                )
                return

        if msg.event == Event.NODE_IS_BORN and bd_metric and seq is not None:
            val = bd_metric.value if type(bd_metric.value) is int else 0
            if not self._bd_seq:
                self._bd_seq = Seq(val)
            else:
                bd_seq = self._bd_seq
                if bd_seq.value != val or bd_seq.next().value != val:
                    logger.warning(f'Incorrect bdSeq at "{msg.key}"')
                self._bd_seq = Seq(val)

            if self._pending:
                logger.warning(
                    f"Lost {len(self._pending)} messages at {self._node_key}, by rebirth"
                )
                if self._oos_task:
                    self._oos_task.cancel()
                self._pending.clear()

            self._seq = Seq(seq)
            self._output.put_nowait(msg)
            return

        if seq is not None and not bd_metric:  # Rest of SpbMessages
            if self._seq is None:
                logger.warning(
                    f'Lost {msg.__class__.__name__} by no birth of "{self._node_key}"'
                )
                return

            _seq = self._seq.next()
            if seq == _seq.value:  # It is tne next message
                self._output.put_nowait(msg)
                self._seq = _seq
                while True:
                    _seq = _seq.next()
                    msg = self._pending.pop(_seq.value, None)
                    if not msg:
                        break
                    self._output.put_nowait(msg)
                    self._seq = _seq
                if self._oos_task:
                    self._oos_task.cancel()
            else:
                self._oos_task = asyncio.create_task(
                    self._raise_out_of_sequence(
                        msg.sending_ts,
                        _seq.value,
                        self._bd_seq.value if self._bd_seq else 0,
                    )
                )
                self._pending[seq] = msg


class HostMessageSession(MessageSession):
    def __init__(
        self,
        key: DeviceKey,
        mqtt_client: MQTT5Client,
        node_encoder: PayloadEncoder,
        host_encoder: PayloadEncoder,
        opts: HostOptions,
        clock: Clock | None = None,
    ):
        if not key.hostname:
            raise ValueError(f'DeviceKey "{key}" is not a correct hostname')
        self._key = key
        self._client = mqtt_client
        self._nencoder = node_encoder
        self._hencoder = host_encoder
        self._opts = opts
        self._clock = clock or UtcClock()

        self._connected = False
        self._messages = asyncio.Queue()

        self._sorters = {}
        self._queue = asyncio.Queue()

    async def establish(self):
        try:
            await self._client.connect(will=self._host_state_is_online_to_mqtt(False))
            await self._client.subscribe(f"spBv1.0/{self._opts.group}/+/+/#", qos=1)
            await self._client.publish(self._host_state_is_online_to_mqtt(True))
            self._connected = True
        except MQTTError as e:
            logger.error("Connection broken by MQTTError")
            logger.exception(e)
            self._connected = False
            raise SessionIsBroken() from e

    def _host_state_is_online_to_mqtt(self, online: bool):
        msg = Message(
            Event.HOST_STATE_HAS_CHANGED,
            self._key,
            online=online,
            sending_ts=self._clock.timestamp(),
        )
        return MQTTMessage(
            msg.get_topic(), self._hencoder.encode(msg.get_payload()), 1, True
        )

    async def terminate(self):
        if not self._connected:
            return

        self._connected = False

        try:
            await self._client.publish(self._host_state_is_online_to_mqtt(False))
            await self._client.disconnect()
        except MQTTError:
            ...

    def is_established(self) -> bool:
        return self._connected

    async def publish(self, msg: Message):
        if msg.event not in (Event.NODE_COMMAND_IS_SENT, Event.DEVICE_COMMAND_IS_SENT):
            raise ValueError(
                f"HostMessageSession only publish commands, not {msg.event} messages"
            )

        msg.sending_ts = self._clock.timestamp()
        try:
            await self._client.publish(
                MQTTMessage(
                    msg.get_topic(), self._nencoder.encode(msg.get_payload()), 0, False
                )
            )
        except MQTTError as e:
            logger.error("Connection broken by MQTTError")
            logger.exception(e)
            self._connected = False
            self._receipt_task = None
            await self._client.disconnect()
            raise SessionIsBroken() from e

    async def subscribe(self) -> AsyncIterable[Message]:
        self._receipt_task = asyncio.create_task(self._recieve_msgs())
        try:
            while True:
                msg = await self._messages.get()
                if isinstance(msg, Exception):
                    raise msg
                yield msg
        finally:
            if self._receipt_task:
                self._receipt_task.cancel()
                try:
                    await self._receipt_task
                except asyncio.CancelledError:
                    ...
                self._receipt_task = None

    def _process_pack(self, msg: Message, seq: int | None, bd_metric: Metric | None):
        if msg.key not in self._sorters:
            self._sorters[msg.key] = _Sorter(
                msg.key, self._messages, self._opts.reorder_time
            )

        self._sorters[msg.key].push_pack(msg, seq, bd_metric)

    async def _recieve_msgs(self):
        try:
            async for mqtt_msg in self._client.messages:
                if "NCMD" in mqtt_msg.topic or "DCMD" in mqtt_msg.topic:
                    continue

                try:
                    payload = self._nencoder.decode(mqtt_msg.payload)
                    bd_metric = None
                    if payload.metrics:
                        for m in payload.metrics:
                            if m.name == "bdSeq":
                                bd_metric = m
                                break
                    msg = Message.construct(mqtt_msg.topic, payload)
                    self._process_pack(msg, payload.seq, bd_metric)
                except Exception as e:
                    logger.error(
                        f"Procesing message from {mqtt_msg.topic}, it will be lost"
                    )
                    logger.exception(e)
        except MQTTError as e:
            logger.error("Recieving node messages, connection broken by MQTTError")
            logger.exception(e)
            self._connected = False
            self._receipt_task = None
            await self._client.disconnect()
            self._messages.put_nowait(SessionIsBroken())
