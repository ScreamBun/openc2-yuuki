# Introduction

Yuuki is a lightweight OpenC2 Consumer. It serves a few purposes:

* Introduce you to OpenC2
* Test against your own OpenC2 Producer
* Ease implementation of Actuator Profiles
* Ease experimentation with different Transports and Serializations

# Yuuki

A Yuuki Consumer is a program that listens for OpenC2 Commands sent from an OpenC2 Producer. It uses received commands to control an actuator(s). The sequence diagram below shows the basic flow of an OpenC2 Message in Yuuki, from receiving a Command to sending a Response.


#### Architecture

```
OpenC2 Producer                            -----------Yuuki (OpenC2 Consumer)-----------       Command
    |                                      |                                           |       Handler
    |                                      |                                           |      (Actuator)
    |                           Transport  |  Serialize /      Validate       Command  |           |
    |                           Endpoint   |  Deserialize         |           Dispatch |           |
    |                              |       |       |              |              |     |           |
    v                              |       |       |              |              |     |           |
                                   v       |       v              v              v     |           v
    |         Network                      |                                           |
    | ---------------------------> |       |                                           |
    |       OpenC2 Command         |       |                                           |
            (serialized)           | ------------> |                                   |
                                           |       | (Python Dict)                     |
                                           |       | -----------> | OpenC2 Command     |
                                           |                      |  (Python Obj)      |
                                           |                      | ------------> |    |
                                           |                                      | -------------> |
                                           |                                      |    |           |
                                           |                                      | <------------- |
                                           |                      | <------------ |    |
                                           |                      | OpenC2 Response    |
                                           |       | <----------- |  (Python Obj)      |
                                           |       | (Python Dict)                     |
                                   | <------------ |                                   |
    |                              |       |                                           |
    | <--------------------------- |       |                                           |
    |      OpenC2 Response                 |                                           |
             (serialized)                  ---------------------------------------------
```

# Installation

Using Python3.8+, install with venv and pip:
```sh
mkdir yuuki
cd yuuki
python3 -m venv venv
source venv/bin/activate
git clone THIS_REPO
pip install ./openc2-yuuki
```

# Examples

Example Consumers using the different transfer protocols, as well as simple Producer scripts have been provided in the `examples` directory.

To demonstrate the OpenC2 Consumers, we'll send a simple OpenC2 Command:

```json
{
    "headers": {
        "request_id": "abc123",
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

After sending a Command like the one above, you should receive a Response similar to the following:

```json
{
    "headers": {
        "request_id": "abc123",
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

## HTTP

Running HTTP locally shouldn't require any configuration. Run the HTTP consumer `http_example.py` in the `examples` directory with:

```sh
python examples/http_example.py
```

### Publish an OpenC2 Command

```sh
source venv/bin/activate
python examples/producers/http_producer.py
```

## MQTT
MQTT requires a little configuration. We'll need to connect to an MQTT broker. Mosquitto is a free broker that's always up (and offers no privacy).

```sh
python examples/mqtt_example.py --host test.mosquitto.org
```

By default, the MQTT Consumer listens for OpenC2 commands on the topic **oc2/cmd**, and publishes its responses to **oc2/rsp**.

### Publish an OpenC2 Command

```sh
source venv/bin/activate
python producers/mqtt_producer.py --host test.mosquitto.org
```

## OpenDXL

| :warning:        | *Support for OpenDXL is experimental. This example may change when the transfer specification for OpenDXL is published.*|
|------------------|:------------------------------------------------------------------------------------------------------------------------|

This example uses both the Event and Request/Response messaging capabilities of OpenDXL to send and receive OpenC2 Messages.

```sh
python examples/opendxl_example.py PATH_TO_YOUR_OPENDXL_CONFIG
```

### Publish an OpenC2 Command

```sh
source venv/bin/activate
python examples/producers/opendxl_producer.py PATH_TO_YOUR_OPENDXL_CONFIG
```
