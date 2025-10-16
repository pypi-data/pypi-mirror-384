import logging
import os
from dataclasses import dataclass

from aiospb.hosts import CommandFollower, Host, MetricsCreator
from aiospb.infra.encoding import JsonPayloadEncoder, ProtobufPayloadEncoder
from aiospb.infra.fs import FSHistorian
from aiospb.infra.inmem import (
    InMemHistorian,
    InMemMinMetricInfoCache,
    InMemReadingStore,
)
from aiospb.infra.paho import MQTTConfig, PahoMQTTClient
from aiospb.messages import HostMessageSession, NodeMessageSession
from aiospb.nodes import EdgeNode, MetricsNetwork, NodeDevice
from aiospb.shared import DeviceKey, HostOptions, NodeOptions

logger = logging.getLogger(__name__)


@dataclass
class HostConfig:
    hostname: str  # it shall not have any "/"
    max_payload_size: int = 0  # unit is bytes
    reorder_time: float = 2.0  # unit is s


def new_host(
    key: str, mqtt_config: MQTTConfig, host_opts: HostOptions
) -> Host:  # pragma: no cover
    """piping to create a sparkplug host from simple parameters"""

    host_key = DeviceKey(key)
    if not host_key.hostname:
        raise ValueError(f'Not allowed name of host "{key}" with a /')
    mqtt_client = PahoMQTTClient(key, mqtt_config)

    session = HostMessageSession(
        host_key,
        mqtt_client,
        ProtobufPayloadEncoder(),
        JsonPayloadEncoder(),
        host_opts,
    )
    cache = InMemMinMetricInfoCache()
    return Host(host_key, session, MetricsCreator(cache), CommandFollower(), host_opts)


def new_edge_of_node(
    key: str,
    mqtt_config: MQTTConfig,
    node_options: NodeOptions,
    metrics_net: MetricsNetwork,
):
    node_key = DeviceKey(key)
    if node_key.hostname or node_key.device_name:
        raise ValueError(f'Not allowed name "{key}" for a node key')

    mqtt_client = PahoMQTTClient(key, mqtt_config)
    session = NodeMessageSession(
        node_key,
        mqtt_client,
        ProtobufPayloadEncoder(),
        JsonPayloadEncoder(),
        node_options,
    )
    if node_options.historian_dir:
        if not os.path.exists(node_options.historian_dir):
            os.makedirs(node_options.historian_dir, exist_ok=True)
        historian = FSHistorian(node_options.historian_dir)
    else:
        logger.info("Creating in memory historian, high risk of loose it")
        historian = InMemHistorian()

    readings_store = InMemReadingStore()
    node = EdgeNode(
        NodeDevice(node_key, metrics_net, readings_store),
        session,
        historian,
        node_options,
    )

    keys = metrics_net.get_device_keys()
    for device_key in keys:
        if device_key.node != node_key:
            node.add_device(NodeDevice(device_key, metrics_net, readings_store))

    return node
