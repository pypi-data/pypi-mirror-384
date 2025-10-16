"""Implementation of ports with file system (files and directories)"""
import logging
import os
import os.path

import aiofiles

from aiospb.nodes.ports import Historian

from ..shared import DataType, DeviceKey, Metric, Quality

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FSHistorian(Historian):
    """Store historical changes in plain files from a operating system"""

    def __init__(self, directory: str):
        self._dir = directory

    def _get_fn(self, key: DeviceKey) -> str:
        return os.path.join(self._dir, key.path.replace("/", "--") + ".csv")

    def _create_line(self, metric: Metric) -> str:
        quality = (
            metric.properties["quality"].value if "quality" in metric.properties else ""
        )
        return f"{metric.timestamp};{metric.value};{metric.data_type.name};{quality};{metric.alias};{metric.name}\n"

    async def load(self, key: DeviceKey) -> list[Metric]:
        metrics = []
        try:
            async with aiofiles.open(self._get_fn(key), "r") as f:
                while True:
                    line = await f.readline()

                    try:
                        values = line[:-1].split(";")

                        if len(values) == 1:
                            break

                        ts, value, datatype, quality, alias, name = values
                        m = Metric(
                            int(ts),
                            DataType[datatype].convert_value(value),
                            DataType[datatype],
                            int(alias),
                            name,
                            is_historical=True,
                        )
                        if quality:
                            m.quality = Quality(int(quality))
                        metrics.append(m)
                    except Exception as e:
                        logger.warning(f'Lost line "{line}" from history')
                        logger.exception(e)
        except FileNotFoundError:
            ...

        return metrics

    async def save(self, key: DeviceKey, metrics: list[Metric]):
        fn = os.path.join(self._dir, key.path.replace("/", "--") + ".csv")
        async with aiofiles.open(fn, "a") as f:
            lines = [self._create_line(metric) for metric in metrics]
            await f.writelines(lines)

    async def clear(self, key: DeviceKey):
        os.remove(self._get_fn(key))

    def get_device_keys(self, node_key: DeviceKey) -> list[DeviceKey]:
        keys = []
        for fn in os.listdir(self._dir):
            if "." in fn:
                key = fn[: fn.index(".")]
                key = key.replace("--", "/")
                device_key = DeviceKey(key)
                if device_key.node == node_key:
                    keys.append(device_key)
        return keys
