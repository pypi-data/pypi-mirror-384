import asyncio
import logging
from collections.abc import Callable, Coroutine
from copy import deepcopy

from aiospb.messages import Event, Message
from aiospb.shared import (
    Clock,
    DataType,
    DeviceKey,
    Metric,
    Quality,
    SparkplugBError,
    UtcClock,
)

from .scanning import Scanner

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from .ports import DeviceConnectionIsBroken, MetricsNetwork, ReadingStore
from .values import MetricInfo, Reading


class NodeDevice:
    """Node Device publish device messages and execute commmands"""

    def __init__(
        self,
        key: DeviceKey,
        metrics_net: MetricsNetwork,
        reading_store: ReadingStore,
        clock: Clock | None = None,
    ):
        self._key = key
        self._control_group = (
            "Device Control/" if self._key.device_name else "Node Control/"
        )
        self._net = metrics_net
        self._readings = reading_store
        self._notify_message = None
        self._clock = clock or UtcClock()

        self._scanners = {}
        self._scan_rate = None
        self._born = False

    @property
    def key(self) -> DeviceKey:
        return self._key

    def add_node_notification(
        self,
        notify_message: Callable[[Message], Coroutine[None, None, None]],
    ):
        self._notify_message = notify_message

    async def rise(self, default_scan_rate: int):
        if not self._notify_message:
            raise ValueError(
                f"Device {self._key} can not start without node to notify messages"
            )

        self._scan_rate = default_scan_rate
        for scanner in self._scanners.values():
            scanner.stop()
        self._scanners.clear()

        dev_infos = await self._net.get_info(self._key)
        if not dev_infos:
            raise Exception(f"Device {self._key} has not metrics to report")

        await self._net.connect_device(self.key)
        metrics = await self._read_birth_metrics(dev_infos, default_scan_rate * 2)
        ts = self._clock.timestamp()
        controls = [
            Metric(ts, False, DataType.Boolean, name=self._control_group + "Rebirth"),
            Metric(ts, False, DataType.Boolean, name=self._control_group + "Restart"),
            Metric(
                ts,
                default_scan_rate,
                DataType.Int32,
                name=self._control_group + "Scan Rate",
            ),
        ]
        if not self._key.device_name:
            controls.append(
                Metric(ts, False, DataType.Boolean, name="Node Control/Reboot")
            )

        for index in range(
            len(metrics)
        ):  # Replace Scan Rate if it is reported by the net
            if metrics[index].name == self._control_group + "Scan Rate":
                self._scan_rate = metrics[index].value
                controls[2] = metrics[index]
                del metrics[index]
                break

        metrics = controls + metrics
        scan_plan = self._construct_scan_plan(metrics)
        for scan_rate, aliases in scan_plan.items():
            if aliases:
                self._scanners[scan_rate] = scanner = Scanner(
                    self._key,
                    aliases,
                    self._net,
                    self._readings,
                    self._recieve_metric_changes,
                    self._clock,
                )
                scanner.start(scan_rate)

        ts = self._clock.timestamp()
        event = Event.DEVICE_IS_BORN if self._key.device_name else Event.NODE_IS_BORN
        await self._notify_message(Message(event, self._key, metrics))
        self._born = True

    def _construct_scan_plan(self, metrics: list[Metric]) -> dict[int, list[int]]:
        scan_rate = metrics[2].value
        if type(scan_rate) is not int:
            raise ValueError(f"Scan Rate shall be integer, not {type(scan_rate)}")

        plan = {scan_rate: []}
        for m in metrics:
            if not m.alias:  # Decided scan only if exist alias
                continue
            if m.properties and "scan_rate" in m.properties:  # Special metrics
                sr = m.properties["scan_rate"]
                if sr.value == 0:
                    continue

                if sr.value not in plan:
                    plan[sr.value] = []

                plan[sr.value].append(m.alias)

            plan[scan_rate].append(m.alias)

        return plan

    async def _read_birth_metrics(
        self, infos: list[MetricInfo], timeout_ms: int
    ) -> list[Metric]:
        tasks = [
            asyncio.create_task(self._read_birth_metric(i, timeout_ms)) for i in infos
        ]
        await asyncio.wait(tasks)
        metrics = []
        readings = []
        for task in tasks:
            metric, reading = task.result()
            if metric.alias:
                readings.append(reading)
            metrics.append(metric)

        await self._readings.set(readings)
        return metrics

    async def _read_birth_metric(
        self, i: MetricInfo, timeout_ms: int
    ) -> tuple[Metric, Reading]:
        try:
            value = await self._clock.wait_for(
                asyncio.create_task(
                    self._net.read(self._key, alias=i.alias, name=i.name), name=i.name
                ),
                timeout_ms,
            )

            reading = Reading(i.name, i.alias, value, i.data_type, Quality.GOOD)
        except TimeoutError:
            reading = Reading(i.name, i.alias, None, i.data_type, Quality.STALE)
        except DeviceConnectionIsBroken:
            reading = Reading(i.name, i.alias, None, i.data_type, Quality.STALE)
        except Exception as e:
            logger.error(f'Reading birth metric of "{i.name}"')
            logger.exception(e)
            reading = Reading(i.name, i.alias, None, i.data_type, Quality.BAD)

        return (i.create_birth_metric(self._clock.timestamp(), reading), reading)

    async def _recieve_metric_changes(self, metrics: list[Metric]):
        if not self._notify_message:
            raise self._no_observer_exception()

        if not self._born:
            raise SparkplugBError(
                f"Stoping sent of changes, device {self._key} hasn't been born"
            )
        event = (
            Event.DEVICE_DATA_HAS_CHANGED
            if self._key.device_name
            else Event.NODE_DATA_HAS_CHANGED
        )
        await self._notify_message(Message(event, self._key, metrics))

    async def die(self):
        for scanner in self._scanners.values():
            scanner.stop()
        self._scanners.clear()

        if not self._notify_message:
            raise self._no_observer_exception()

        event = Event.DEVICE_HAS_DIED if self._key.device_name else Event.NODE_HAS_DIED
        await self._notify_message(Message(event, self._key))
        await self._net.disconnect_device(self.key)
        self._born = False

    def _no_observer_exception(self):
        return SparkplugBError("There is no EdgeNode observing device")

    async def write_metrics(self, metrics: list[Metric], timeout_ms: int):
        """Write to device the metrics in order"""
        if not self._born:
            raise SparkplugBError(f"Device {self._key} has't been born")

        names = [m.name for m in metrics]
        if f"{self._control_group}Scan Rate" in names:
            val = metrics[names.index(f"{self._control_group}Scan Rate")].value
            if type(val) is int:
                await self._set_scan_rate(val)

        readings = []
        metrics = deepcopy(metrics)
        dead_line = self._clock.timestamp() + timeout_ms
        has_failed = False
        for metric in metrics:
            if has_failed:  # When firt
                metric.quality = Quality.BAD
                metric.timestamp = self._clock.timestamp()
                continue

            quality = Quality.GOOD
            try:
                task = asyncio.create_task(
                    self._net.write(
                        self._key, metric.value, alias=metric.alias, name=metric.name
                    )
                )
                timeout_ms = dead_line - self._clock.timestamp()
                if timeout_ms <= 0:
                    raise TimeoutError()
                await self._clock.wait_for(task, timeout_ms)
            except TimeoutError:
                quality = Quality.STALE
            except Exception as e:
                logger.error(
                    f"Writing to {metric.name}:{metric.alias}, value {metric.value}"
                )
                logger.exception(e)
                has_failed = True
                quality = Quality.BAD

            metric.timestamp = self._clock.timestamp()
            metric.quality = quality
            readings.append(
                Reading(
                    metric.name,
                    metric.alias,
                    metric.value,
                    metric.data_type,
                    quality=quality,
                )
            )

        await self._recieve_metric_changes(metrics)
        await self._readings.set(readings)

    async def _set_scan_rate(self, value: int):
        if value == self._scan_rate:
            return
        scanner = self._scanners.pop(self._scan_rate)
        if scanner:
            scanner.stop()
            scanner.start(value)
