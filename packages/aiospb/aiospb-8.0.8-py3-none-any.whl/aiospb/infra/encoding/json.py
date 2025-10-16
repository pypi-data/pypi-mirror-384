import json

from aiospb.messages import Payload, PayloadEncoder
from aiospb.shared import Metric


class JsonPayloadEncoder(PayloadEncoder):
    """Encoder of messages for testing purposes"""

    def encode(self, payload: Payload) -> bytes:
        """Convert a payload dict to a string for publishing"""
        if payload.online is not None:
            data = {"timestamp": payload.timestamp, "online": payload.online}
        else:
            data = {"timestamp": payload.timestamp, "seq": payload.seq}
            data["metrics"] = [metric.as_dict() for metric in payload.metrics]

        return json.dumps(data).encode("utf-8")

    def decode(self, b: bytes) -> Payload:
        """Convert payload to a payload dict"""

        data = json.loads(b.decode("utf-8"))
        if "online" in data:
            return Payload(data["timestamp"], online=data["online"])

        metrics = [Metric.from_dict(item) for item in data["metrics"]]
        return Payload(timestamp=data["timestamp"], metrics=metrics, seq=data["seq"])
