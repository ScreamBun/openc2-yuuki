import json
import cbor2

serializations = frozenset(['json', 'cbor'])

_decode = {
    'json': json.loads,
    'cbor': cbor2.loads
}

_encode = {
    'json': json.dumps,
    'cbor': cbor2.dumps
}


def deserialize(data, encoding):
    return _decode[encoding](data)


def serialize(data, encoding):
    return _encode[encoding](data)
