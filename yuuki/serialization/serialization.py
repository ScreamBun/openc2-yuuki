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


def deserialize(data, encoding):
    return decode[encoding](data)


def serialize(data, encoding):
    return encode[encoding](data)
