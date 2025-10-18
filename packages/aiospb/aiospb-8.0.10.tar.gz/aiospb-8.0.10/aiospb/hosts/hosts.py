import asyncio
import logging
from typing import Callable, Coroutine

from aiospb.messages import Event, Message, MessageSession
from aiospb.messages.ports import SessionIsBroken
from aiospb.shared import Clock, UtcClock

from ..shared import DataType, DeviceKey, HostOptions, Metric
from .commands import CommandFollower, MetricsCreator
from .values import CommandRequest, CommandResponse, WritingResolution

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


_CTR_NAMES = (
    "Node Control/Rebirth",
    "Node Control/Restart",
    "Node Control/Reboot",
    "Device Control/Rebirth",
    "Device Control/Restart",
    "Device Control/Reboot",
)


class Host:
    """Host to notify messages to observers and execute commands"""

    def __init__(
        self,
        key: DeviceKey,
        host_session: MessageSession,
        metrics_creator: MetricsCreator,
        command_follower: CommandFollower,
        options: HostOptions,
        clock: Clock | None = None,
    ):
        self._key = key
        self._session = host_session
        self._creator = metrics_creator
        self._follower = command_follower
        self._opts = options

        self._clock = clock or UtcClock()

        self._observers = {}
        self._incomming = None

    async def _subscribe_to_nodes(self):
        try:
            async for msg in self._session.subscribe():
                if msg.event == Event.OUT_OF_SEQUENCE:
                    logger.warning(
                        f"Found out of sequence at {msg.key}, sending rebirth..."
                    )
                    await self._session.publish(
                        Message(
                            Event.NODE_COMMAND_IS_SENT,
                            msg.key,
                            [
                                Metric(
                                    msg.sending_ts,
                                    True,
                                    DataType.Boolean,
                                    name="Node Control/Rebirth",
                                )
                            ],
                        )
                    )
                    continue

                await self._notify_to_observers(msg)

        except SessionIsBroken:
            await self._notify_to_observers(
                Message(Event.HOST_STATE_HAS_CHANGED, self._key, online=False)
            )
            self._incomming = None
        except asyncio.CancelledError:
            if self._incomming:
                self._incomming.cancel()
                try:
                    await self._incomming
                except asyncio.CancelledError:
                    ...
        except Exception as e:
            logger.warning("Error while procesing message")
            logger.exception(e)

            if self._incomming:
                self._incomming.cancel()
                try:
                    await self._incomming
                except asyncio.CancelledError:
                    ...
            self._incomming = asyncio.create_task(self._subscribe_to_nodes())
            raise e

    async def _notify_to_observers(self, msg: Message):
        timeout = self._opts.notify_timeout
        tasks = [
            asyncio.create_task(callback(msg), name=key)
            for key, callback in self._observers.items()
        ]
        _, pending = await asyncio.wait(tasks, timeout=timeout)
        for t in pending:
            logger.warning(
                f'Notification of {msg.event} from "{msg.key.path}" to {t.get_name()} is cancelled'
            )
            t.cancel()
            # try:
            #     await t
            # except asyncio.CancelledError:
            #     ...

    def with_options(self, value: HostOptions):
        self._opts = value

    async def establish_session(self):
        if self._incomming:
            self._incomming.cancel()
            self._incomming = None

        await self._session.establish()

        if "follower" not in self._observers:
            self.add_observer("follower", self._follower.update_command_pipes)

        if "creator" not in self._observers:
            self.add_observer("creator", self._creator.update_metric_pars)

        self._incomming = asyncio.create_task(self._subscribe_to_nodes())

    async def terminate_session(self):
        await self._terminate()
        await self._session.terminate()

    async def execute_command(self, req: CommandRequest) -> CommandResponse:
        if not self._session.is_established():
            return CommandResponse(
                self._clock.timestamp(),
                [WritingResolution.HostIsOffline] * len(req.requests),
            )

        metrics = await self._creator.construct_writing_metrics(req)
        if DataType.Unknown in [m.data_type for m in metrics]:
            return CommandResponse(
                self._clock.timestamp(),
                [
                    WritingResolution.MetricNotFound
                    if m.data_type == DataType.Unknown
                    else WritingResolution.Cancelled
                    for m in metrics
                ],
            )
        event = (
            Event.DEVICE_COMMAND_IS_SENT
            if req.key.device_name
            else Event.NODE_COMMAND_IS_SENT
        )

        names = [m.name for m in metrics]
        for cname in _CTR_NAMES:
            if cname in names:
                if len(names) > 1:
                    logger.error(
                        f"Not possible to send control command {cname} with other metrics"
                    )
                    return CommandResponse(
                        self._clock.timestamp(),
                        [WritingResolution.BadWriting] * len(names),
                    )

                try:
                    await self._session.publish(Message(event, req.key, metrics))
                    return CommandResponse(
                        self._clock.timestamp(), [WritingResolution.GoodWriting]
                    )
                except Exception as e:
                    logger.error(f"Failed to send control {cname} to {req.key}")
                    logger.exception(e)
                    return CommandResponse(
                        self._clock.timestamp(), [WritingResolution.BadWriting]
                    )

        try:
            await self._session.publish(Message(event, req.key, metrics))
        except SessionIsBroken:
            return CommandResponse(
                self._clock.timestamp(),
                [WritingResolution.HostIsOffline] * len(metrics),
            )

        return await self._follower.follow_command(
            req.key, metrics, req.writing_timeout
        )

    def add_observer(
        self,
        key: str,
        callback: Callable[[Message], Coroutine[None, None, None]],
    ):
        self._observers[key] = callback

    async def _terminate(self):
        if self._incomming:
            self._incomming.cancel()
            try:
                await self._incomming
            except asyncio.CancelledError:
                ...
            self._incomming = None
