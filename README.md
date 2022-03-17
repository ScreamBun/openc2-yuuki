# Yuuki

## Introduction

Yuuki is a framework for creating OpenC2 Consumers. It serves a few purposes:

* Provide an introduction to OpenC2
* Provide an OpenC2 Consumer for OpenC2 Producers to test against
* Facilitate experimentation with different Actuator profiles, transfer protocols and message serializations


## Consumers

A Consumer is initialized with a rate limit and a list of OpenC2 language versions that it supports, as well as an optional list of [Actuators](#actuators) and an optional list of [Serializations](#serializations).

```python
from yuuki import Consumer

consumer = Consumer(rate_limit=60, versions=['1.0'], actuators=[], serializations=[])
```

OpenC2 Commands are processed using the `process_command` method which takes a serialized OpenC2 Command as well as a string identifying the serialization protocol and returns a serialized Response.

```python
consumer.process_command(command, 'json')
```

The Consumer also provides a method to create a serialized Response message without processing a Command.

```python
from yuuki import OpenC2RspFields

consumer.create_response_msg(response_body=OpenC2RspFields(), encode='json')
```


## Actuators

By default, the Consumer only supports a single Command: `query features`.
The set of Commands supported by the Consumer can be extended with Actuators, which can be added to the Consumer either during or after its initialization.

For example, see the sample implementation of an Actuator based on the [Stateless Packet Filtering](https://docs.oasis-open.org/openc2/oc2slpf/v1.0/oc2slpf-v1.0.html) Actuator profile in `examples/actuators/slpf.py`

An Actuator is identified by a string representing the namespace identifier (nsid) of its Actuator profile.
[Stateless Packet Filtering](https://docs.oasis-open.org/openc2/oc2slpf/v1.0/oc2slpf-v1.0.html) is a standard Actuator profile with the nsid: `slpf`.
The nsids of nonstandard Actuator profiles must be prefixed with `x-`.

```python
from yuuki import Actuator

example = Actuator(nsid='x-example')
```

After an Actuator is initialized, functions that correspond to Commands that the Actuator supports should be added to it.
These functions should have an `OpenC2CmdFields` object as their only parameter and return an `OpenC2RspFields` object.

The `pair` decorator is used to indicate to the Actuator which Command a function is intended to support.

```python
from yuuki import OpenC2CmdFields, OpenC2RspFields, StatusCode

@example.pair('action', 'target')
def example_command(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    return OpenC2RspFields(status=StatusCode.OK)
```

Functions for Commands that are specified in the Actuator profile, but not implemented by the Actuator should set the `implemented` argument to `False`.

```python
@example.pair('action', 'target', implemented=False)
def unsupported_command(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    pass
```


## Serializations

Serialization objects are used to add support for different methods of decoding and encoding messages to the Consumer.
They are initialized with three arguments: the string that will be used to identify the protocol in OpenC2 Messages, a function for decoding messages, and a function for encoding messages. The Consumer class comes with support for JSON.
```python
import json
from yuuki import Serialization

Serialization(name='json', deserialize=json.loads, serialize=json.dumps)
```


## Installation

Using Python3.8+, install with venv and pip:
```sh
mkdir yuuki
cd yuuki
python3 -m venv venv
source venv/bin/activate
git clone THIS_REPO
pip install ./openc2-yuuki
```


## Examples

An example Consumer utilizing different transport protocols, as well as sample Producer scripts have been provided in the `examples` directory.

To demonstrate the OpenC2 Consumer, each Producer sends an OpenC2 Command similar to the following:

```json
{
    "headers": {
        "request_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
        "created": 1619554273604,
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "query",
                "target": {
                    "features": []
                }
            }
        }
    }
}
```

After sending the Command, the Producer should receive a Response similar to the following:

```json
{
    "headers": {
        "request_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
        "created": 1619554273604,
        "to": "Producer1",
        "from": "yuuki"
    },
    "body": {
        "openc2": {
            "response": {
                "status": 200
            }
        }
    }
}
```

The Examples should be run under the virtual environment created during installation:
```sh
source venv/bin/activate
```

### HTTP

#### Start Consumer:
```sh
python examples/http_example.py
```

#### Publish an OpenC2 Command:
```sh
python examples/producers/http_producer.py
```

### MQTT
A connection to an MQTT broker is required. A publicly available MQTT broker is hosted at [test.mosquitto.org](https://test.mosquitto.org).

#### Start Consumer:
```sh
python examples/mqtt_example.py --host test.mosquitto.org
```

#### Publish an OpenC2 Command:
```sh
python producers/mqtt_producer.py --host test.mosquitto.org
```

### OpenDXL

| :warning:        | *Support for OpenDXL is experimental*|
|------------------|:-------------------------------------|

This example uses both the Event and Request/Response messaging capabilities of OpenDXL to send and receive OpenC2 Messages.

An OpenDXL configuration file is required to run these examples.

#### Start Consumer:
```sh
python examples/opendxl_example.py PATH_TO_OPENDXL_CONFIG
```

#### Publish an OpenC2 Command:
```sh
python examples/producers/opendxl_producer.py PATH_TO_OPENDXL_CONFIG
```
