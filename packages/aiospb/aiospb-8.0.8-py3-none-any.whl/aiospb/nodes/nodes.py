"""Main components of sparkplug standard"""

import asyncio
import datetime
import logging
import subprocess
import sys

from aiospb import exponential_retry
from aiospb.messages import Event, Message, MessageSession, SessionIsBroken
from aiospb.shared import DeviceKey, Metric, NodeOptions

from .devices import NodeDevice
from .ports import Historian

logger = logging.getLogger(__name__)


class DeviceAlreadyRisen(Exception):
    """The device is rising now or has been recently risen"""


class EdgeNode:
    """Gateway connected to mqtt and to one or more hardware devices"""

    def __init__(
        self,
        root: NodeDevice,
        session: MessageSession,
        historian: Historian,
        options: NodeOptions | None = None,
    ):
        self._root = root
        self._key = root.key
        root.add_node_notification(self._recieve_device_message)

        self._session = session
        self._historian = historian
        self._opts = options or NodeOptions
        self._devices_with_history = set(historian.get_device_keys(root.key))
        self._primary = DeviceKey(self._opts.primary) if self._opts.primary else None

        # State variables
        self._devices = {}
        self._incomming = None
        self._connecting = False
        self._hosts_online = set()

        self._messages = asyncio.Queue()

    @exponential_retry(max_retries=20, base_delay=3)
    async def establish_session(self):
        """Establish MessageSession to process messages (inputs & outputs)"""
        self._connecting = True

        await self._session.establish()

        if self._incomming and not self._incomming.done():  # Remove old subscription
            self._incomming.cancel()
        self._incomming = asyncio.create_task(self._recieve_host_messages())

        self._connecting = False

    def has_session_established(self):
        return self._session.is_established()

    async def _rise_all(self):
        try:
            await self._root.rise(self._opts.scan_rate)
            for device in self._devices.values():
                await device.rise(self._opts.scan_rate)
        except DeviceAlreadyRisen:
            pass

    async def _recieve_host_messages(self):
        try:
            async for msg in self._session.subscribe():
                try:
                    match msg.event:
                        case Event.HOST_STATE_HAS_CHANGED:
                            if msg.online:
                                self._hosts_online.add(msg.key)
                                logger.info(f"Recieved host {msg.key} is online")
                                await self._rise_all()
                                logger.info("Raised all devices!!")
                            else:
                                self._hosts_online.remove(msg.key)

                        case Event.DEVICE_COMMAND_IS_SENT:
                            if msg.key not in self._devices:
                                continue

                            await self._execute_device_command(
                                msg.key,
                                msg.metrics,
                                int(self._opts.write_timeout * 1000),
                            )

                        case Event.NODE_COMMAND_IS_SENT:
                            await self._execute_node_command(
                                msg.metrics, int(self._opts.write_timeout * 1000)
                            )
                except Exception as e:
                    logger.error(
                        f"Processing message {msg.event}, lost by unexpected exception"
                    )
                    logger.exception(e)
        except SessionIsBroken:
            logger.warning(
                "Session is broken while recieving host messages, reconnecting..."
            )
            if not self._connecting:
                await self.establish_session()
        except Exception as e:
            logger.error(f"Digesting message, restarting subscription")
            logger.exception(e)
            self._incomming = asyncio.create_task(self._recieve_host_messages())

    async def _execute_node_command(self, metrics: list[Metric], timeout_ms: int):
        if not metrics:
            return
        names = [m.name for m in metrics]
        dead_time = int(datetime.datetime.now().timestamp() * 1000) + timeout_ms
        if "Node Control/Rebirth" in names:
            idx = names.index("Node Control/Rebirth")
            await self._execute_node_command(metrics[:idx], timeout_ms)
            await self._rise_all()
            logger.info(f"Executed rebirth of node")

            if idx < len(metrics) - 1:
                timeout_ms = dead_time - int(datetime.datetime.now().timestamp() * 1000)
                await self._execute_node_command(metrics[idx + 1 :], timeout_ms)
            return

        if "Node Control/Restart" in names:
            idx = names.index("Node Control/Restart")
            await self._execute_node_command(metrics[:idx], timeout_ms)
            await self.terminate_session()
            logger.info(f"Executed restart of node")
            sys.exit()
            return

        if "Node Control/Reboot" in names:
            idx = names.index("Node Control/Reboot")

            await self._execute_node_command(metrics[:idx], timeout_ms)
            await self.terminate_session()
            logger.info(f"Executing clean reboot of node")
            subprocess.run("shutdown -r now", check=True, capture_output=True)
            return

        await self._root.write_metrics(metrics, timeout_ms)

        logger.info(f"Executed command at node with {len(metrics)} writings")

    async def _execute_device_command(
        self, key: DeviceKey, metrics: list[Metric], timeout_ms: int
    ):
        if not metrics:
            return

        dev = self._devices[key]
        names = [m.name for m in metrics]
        dead_time = int(datetime.datetime.now().timestamp() * 1000) + timeout_ms
        if "Device Control/Rebirth" in names:
            idx = names.index("Device Control/Rebirth")
            await self._execute_device_command(key, metrics[:idx], timeout_ms)
            await dev.rise(self._opts.scan_rate)
            logger.info(f"Executed rebirth of device {key}")
            if idx < len(metrics) - 1:
                timeout_ms = dead_time - int(datetime.datetime.now().timestamp() * 1000)
                await self._execute_device_command(key, metrics[idx + 1 :], timeout_ms)
            return

        if "Device Control/Restart" in names:
            idx = names.index("Device Control/Restart")
            await self._execute_device_command(key, metrics[:idx], timeout_ms)
            await dev.die()
            await dev.rise(self._opts.scan_rate)
            logger.info(f"Executed restart of device {key}")
            if idx < len(metrics) - 1:
                timeout_ms = dead_time - int(datetime.datetime.now().timestamp() * 1000)
                await self._execute_device_command(key, metrics[idx + 1 :], timeout_ms)
            return

        await dev.write_metrics(metrics, timeout_ms)
        logger.info(f"Executed command at device {key} with {len(metrics)} writings")

    async def terminate_session(self):
        if self._incomming:
            self._incomming.cancel()
            self._incomming = None

        for device in self._devices.values():
            await device.die()

        await self._root.die()
        await self._session.terminate()

    def _can_publish_changes(self):
        return self._session.is_established() and (
            (self._primary and self._primary in self._hosts_online)
            or (not self._primary and self._hosts_online)
        )

    async def _save_to_historian(self, msg: Message):
        await self._historian.save(msg.key, msg.metrics)
        self._devices_with_history.add(msg.key)

    async def _publish_with_history(self, msg: Message):
        with_history = False
        try:
            history = await self._historian.load(msg.key)
            msg.metrics = history + msg.metrics
            with_history = True
        except Exception as e:
            logger.error(f"Lost history loading, but keep file")
            logger.exception(e)

        await self._session.publish(msg)
        logger.info(f"Published {msg.event} with {len(msg.metrics)} metrics")

        if with_history:
            await self._historian.clear(msg.key)
            self._devices_with_history.remove(msg.key)

    async def _recieve_device_message(self, msg: Message):
        try:
            if msg.event in (
                Event.NODE_DATA_HAS_CHANGED,
                Event.DEVICE_DATA_HAS_CHANGED,
            ):
                if not self._can_publish_changes():
                    await self._save_to_historian(msg)
                    logger.info(f"Saved {len(msg.metrics)} metrics to historiang")
                    return

                if msg.key in self._devices_with_history:
                    await self._publish_with_history(msg)
                    logger.info(f"Published metrics with history")
                    return

            await self._session.publish(msg)
            logger.info(f"Published {msg.event} with {len(msg.metrics)} metrics")

        except SessionIsBroken:
            logger.warning("Session has been broken when publishing, restablishing...")
            if not self._connecting:
                await self.establish_session()
        except Exception as e:
            logger.error(
                f"Unexpected exception, message {type(msg)} will not published"
            )
            logger.exception(e)

    def add_device(self, device: "NodeDevice"):
        """Add a Node Device to a Node"""
        device.add_node_notification(self._recieve_device_message)
        self._devices[device.key] = device
