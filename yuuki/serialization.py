import json
import cbor2

decode = {
    'json': json.loads,
    'cbor': cbor2.loads
}

encode = {
    'json': json.dumps,
    'cbor': cbor2.dumps
}


def deserialize(data, encoding) -> dict:
    message = decode[encoding](data)
    if not isinstance(message, dict):
        raise TypeError
    return message


def serialize(data, encoding):
    return encode[encoding](data)
