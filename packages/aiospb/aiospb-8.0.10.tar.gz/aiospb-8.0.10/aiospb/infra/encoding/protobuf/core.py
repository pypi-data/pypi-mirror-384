from aiospb.messages import EncodingError, Payload, PayloadEncoder
from aiospb.shared import DataType, Metric, ValueType

from . import sparkplug_pb2 as pb2


class _ValueConversor:
    _VALUES = {
        "String": "string_value",
        "UInt8": "int_value",
        "UInt16": "int_value",
        "UInt32": "int_value",
        "UInt32": "int_value",
        "UInt64": "long_value",
        "Float": "float_value",
        "Double": "double_value",
        "Boolean": "boolean_value",
        "Bytes": "bytes_value",
    }

    def save_value(
        self,
        message: pb2.Payload.Metric | pb2.Payload.PropertyValue,
        type_str: str,
        value: ValueType,
    ):
        try:
            if value is None:
                setattr(message, "is_null", True)
            elif type_str == "Int64":
                setattr(message, "long_value", int(value) & 0xFFFFFFFFFFFFFFFF)
            elif type_str == "UInt64":
                setattr(message, "long_value", int(value) & 0xFFFFFFFFFFFFFFFF)
            elif type_str.startswith("Int"):
                setattr(message, "int_value", int(value) & 0xFFFFFFFF)
            elif type_str.startswith("UInt"):
                setattr(message, "int_value", int(value) & 0xFFFFFFFF)
            else:
                setattr(message, self._VALUES[type_str], value)
        except KeyError:
            raise EncodingError(f"Not possible to save value {value} at {message}")
        except ValueError:
            raise EncodingError(f"Not possible to save value {value} as integer")

    def load_value(self, message, type_str: str) -> ValueType:
        if message.HasField("is_null"):
            return
        if type_str == "Int64":
            value = getattr(message, "long_value")
            return value - 0x10000000000000000 if value > 0x7FFFFFFFFFFFFFFF else value
        if type_str == "UInt64":
            return getattr(message, "long_value")
        elif type_str.startswith("Int"):
            value = getattr(message, "int_value")
            return value - 0x100000000 if value > 0x7FFFFFFF else value
        else:
            return getattr(message, self._VALUES[type_str])


class ProtobufPayloadEncoder(PayloadEncoder):
    def __init__(self):
        self._conversor = _ValueConversor()

    def encode(self, payload: Payload) -> bytes:
        """Convert a message to a payload"""
        pb_payload = pb2.Payload()

        try:
            pb_payload.timestamp = payload.timestamp
            if payload.seq is not None:
                pb_payload.seq = payload.seq
            for metric in payload.metrics:
                pb_metric = pb_payload.metrics.add()
                pb_metric.datatype = metric.data_type.value
                pb_metric.timestamp = metric.timestamp
                self._conversor.save_value(
                    pb_metric, metric.data_type.name, metric.value
                )
                if metric.name:
                    pb_metric.name = metric.name
                if metric.alias:
                    pb_metric.alias = metric.alias
                if metric.is_historical:
                    pb_metric.is_historical = True
                if metric.is_transient:
                    pb_metric.is_transient = True
                if metric.properties:
                    values = []
                    for prop in metric.properties.values():
                        if prop.value is None:
                            value = pb2.Payload.PropertyValue(
                                type=prop.data_type.value, is_null=True
                            )
                        else:
                            value = pb2.Payload.PropertyValue(type=prop.data_type.value)
                            self._conversor.save_value(
                                value, prop.data_type.name, prop.value
                            )
                        values.append(value)

                    pb_metric.properties.CopyFrom(
                        pb2.Payload.PropertySet(
                            keys=tuple(metric.properties.keys()), values=values
                        )
                    )

            return pb_payload.SerializeToString()
        except Exception as e:
            raise EncodingError("Error when encoding") from e

    def _decode_metric(self, spb_metric: pb2.Payload.Metric) -> Metric:
        dump = {
            "timestamp": spb_metric.timestamp,
            "dataType": DataType(spb_metric.datatype).name,
        }
        if spb_metric.HasField("is_null"):
            value = None
        else:
            value = self._conversor.load_value(
                spb_metric, DataType(spb_metric.datatype).name
            )
        dump["value"] = value

        if spb_metric.HasField("name"):
            dump["name"] = spb_metric.name
        if spb_metric.HasField("alias"):
            dump["alias"] = spb_metric.alias
        if spb_metric.HasField("is_historical"):
            dump["is_historical"] = spb_metric.is_historical
        if spb_metric.HasField("is_transient"):
            dump["is_transient"] = spb_metric.is_transient
        if spb_metric.HasField("properties"):
            properties = spb_metric.properties
            dump["properties"] = {
                key: {
                    "dataType": DataType(prop.type),
                    "value": self._conversor.load_value(prop, DataType(prop.type).name),
                }
                for key, prop in zip(properties.keys, properties.values)
            }
        return Metric.from_dict(dump)

    def decode(self, b: bytes) -> Payload:
        """Convert payload to a message object"""
        try:
            pb_payload = pb2.Payload.FromString(b)
        except Exception as e:
            raise EncodingError("Error when decoding") from e

        data = {"timestamp": pb_payload.timestamp, "metrics": []}
        if pb_payload.HasField("seq"):
            data["seq"] = pb_payload.seq
        for spb_metric in pb_payload.metrics:
            data["metrics"].append(self._decode_metric(spb_metric))

        return Payload(**data)
