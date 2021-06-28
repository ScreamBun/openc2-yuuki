# Introduction

Yuuki is a lightweight OpenC2 framework that comes with example Consumers, all built on an extensible library, with default support for **HTTP** and **MQTT** protocols. It serves a few purposes:

* Provide [ready-made examples](#example-http) to
  * Introduce you to OpenC2
  * Test against your own OpenC2 Producer
* Provide a library to
  * Ease implementation of Actuator Profiles
  * Ease experimentation with different Transports, Serializations and Validators

To jump right in, head over to the examples directory, or follow along below for a guided tour.

# Yuuki

A Yuuki Consumer is a program that listens for OpenC2 Commands sent from an OpenC2 Producer. It uses received commands to control an actuator(s). The sequence diagram below shows the basic flow of an OpenC2 Message in Yuuki, from receiving a Command to sending a Response.


#### Architecture

```
OpenC2 Producer               ----------------- Yuuki (OpenC2 Consumer)-----------------       Command
    |                         |                                                        |       Handler
    |                         |                                                        |      (Actuator)
    |                         | Transport     Serialize /      Validate       Command  |           |
    |                         | Endpoint      Deserialize         |           Dispatch |           |
    |                         |    |               |              |              |     |           |
    v                         |    |               |              |              |     |           |
                              |    v               v              v              v     |           v
    |         Network         |                                                        |              
    | ------------------------|--> |                                                   |              
    |       OpenC2 Command    |    |                                                   |              
            (serialized)      |    | ------------> |                                   |              
                              |                    | (Python Dict)                     |            
                              |                    | -----------> | OpenC2 Command     |              
                              |                                   |  (Python Obj)      |              
                              |                                   | ------------> |    |              
                              |                                                   |    |              
                              |                                                   | ---|---------> |
                              |                                                   |    |           |
                              |                                                   | <--|---------- |
                              |                                                   |    |              
                              |                    | <--------------------------- |    |             
                              |                    |        OpenC2 Response            |              
                              |    | <------------ |          (Python Obj)             |     
    |                         |    |                                                   |              
    | <-----------------------|--- |                                                   |              
    |      OpenC2 Response    |                                                        |              
             (serialized)     ----------------------------------------------------------              

```

Yuuki is designed so that any of these steps can be customized or replaced.

* Want to use **MQTT**, **HTTP** or even add a **new transport**? 
* Want to serialize your messages with **CBOR** instead of **JSON**?
* Want to use a **schema** validation tool, instead of simple Python functions to validate OpenC2 Messages?

For all of these goals, the solution is to swap out what you'd like replace. Each step is independent of the others.

For example, look at how the main OpenC2 Consumer is constructed in **http_example.py** in the *examples* folder:

```python
consumer = Consumer(cmd_handler = CmdHandler(validator = validate_and_convert), transport = Http(http_config))
```

See the **Http** and **validate_and_convert** arguments? Simply replace any of those with a library of your own; just as long as you follow the same Yuuki interface.

Before getting ahead of ourselves with customization, let's just run a simple example: HTTP

# Installation

Using Python3.7+, install with venv and pip:
```sh
mkdir yuuki
cd yuuki
python3.7 -m venv venv
source venv/bin/activate
git clone THIS_REPO
pip install ./openc2-yuuki
```

# Example: HTTP

Running HTTP locally shouldn't require any configuration. Run the HTTP consumer `http_example.py` in the *examples* directory with

```sh
python http_example.py
```

## Test HTTP Transport

### Publish an OpenC2 Command
In a new terminal window, go back to the root "yuuki" folder, then enable the virtual environment and start a Python shell.

```sh
source venv/bin/activate
python
```

Copy this text into the shell.

```python
import time
import json

import requests

query_features = {
    "headers": {
        "request_id": "abc123",
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "query",
                "target": {
                    "features": [
                        "profiles"
                    ]
                }
            }
        }
    }
}

headers = {"Content-Type": "application/openc2-cmd+json;version=1.0"}

response = requests.post("http://127.0.0.1:9001", json=query_features, headers=headers, verify=False)

print(json.dumps(response.json(), indent=4))

```

Because we're testing locally, you should instantly see the OpenC2 Response, similar to this.

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
                "status": 200,
                "status_text": "OK - the Command has succeeded.",
                "results": {
                    "profiles": [
                        "slpf",
                        "x-acme"
                    ]
                }
            }
        }
    }
}
```

*When done with this Producer shell, type exit() and hit enter*

Success! The Yuuki Consumer successfully received an OpenC2 Command, then returned an OpenC2 Response.

### Shut Down
In the Yuuki Consumer shell, hit CTRL-C to stop the process.

# Example: MQTT
MQTT requires a little configuration. We'll need to connect to an MQTT broker. Mosquitto is a free broker that's always up (and offers no privacy).

At the bottom of `mqtt_example.py` in the *examples* directory, supply the socket address for the broker.

```python
    mqtt_config = MqttConfig(broker=BrokerConfig(socket='test.mosquitto.org:1883'))
```

Save your file and start the example:

```sh
python mqtt_example.py
```

That's it! Your OpenC2 MQTT Consumer is ready for any published commands. If you're familiar with MQTT, by default Yuuki listens for OpenC2 commands on the topic **yuuki_user/oc2/cmd**, and publishes its responses to **yuuki_user/oc2/rsp**. Next, we'll write a quick script to make sure it's working.

If you'd like to change the topics, you can like so:

```python
    mqtt_config = MqttConfig(
                    ...
                    subscriptions=[Subscription('subscribe/to/command/topic', 1),
                                   Subscription('another/command/topic', 0)],
                    publishes=[Publish('publish/responses/here', 0),
                               Publish('another/response/topic', 3)])
```

## Test MQTT Transport

### Publish an OpenC2 Command
In a new terminal window, go back to the root "yuuki" folder, then enable the virtual environment and start a Python shell.

```sh
source venv/bin/activate
python
```

Copy this text into the shell.

```python
import time
import json

from paho.mqtt import client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.subscribeoptions import SubscribeOptions

payload_json = {
    "headers": {
        "request_id": "abc123",
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "query",
                "target": {
                    "features": [
                        "profiles"
                    ]
                }
            }
        }
    }
}

oc2_properties = Properties(PacketTypes.PUBLISH)
oc2_properties.PayloadFormatIndicator = 1
oc2_properties.ContentType = "application/openc2"
oc2_properties.UserProperty = [("msgType", "req"), ("encoding", "json")]


def on_message(client, userdata, msg):
    print(json.dumps(json.loads(msg.payload), indent=4))
    client.disconnect()


mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
mqtt_client.on_message = on_message
mqtt_client.connect(host="test.mosquitto.org", port=1883, keepalive=60, clean_start=False)
mqtt_client.subscribe(topic="yuuki/oc2/rsp",
                      options=SubscribeOptions(qos=1, noLocal=True, retainAsPublished=True, retainHandling=0))
mqtt_client.publish(topic="yuuki/oc2/cmd", payload=json.dumps(payload_json),
                    qos=1, retain=False, properties=oc2_properties)
mqtt_client.loop_forever()

```

*When done with this Producer shell, type exit() and hit enter*

### Check Results
There should be a JSON OpenC2 Response message, similar to this:
```json
{
    "headers": {
        "request_id": "abc123",
        "created": 1617026741390,
        "to": "Producer1",
        "from": "yuuki"
    },
    "body": {
        "openc2": {
            "response": {
                "status": 200,
                "status_text": "OK - the Command has succeeded.",
                "results": {
                    "profiles": [
                        "slpf",
                        "x-acme"
                    ]
                }
            }
        }
    }
}
```

Success! The Yuuki Consumer successfully received an OpenC2 Command, then published an OpenC2 Response.

# Example: OpenDXL

This example tests sending OpenC2 commands using both the Event and Request/Response messaging capabilities of OpenDXL.

To configure Yuuki to use OpenDXL, set `CONFIG_FILE` in `oc2_opendxl.py` to the path where your `dxlclient.config` file is located.

Then run the example found in the `examples` directory:

```sh
python opendxl_example.py
```

## Test OpenDXL Transport

### Publish an OpenC2 Command
In a new terminal window, go back to the root "yuuki" folder, then enable the virtual environment and start a Python shell.

```sh
source venv/bin/activate
python
```

Set `CONFIG_FILE` to the path where your `dxlclient.config` file is located, and copy this text into the shell.

```python
import time
import json

from dxlclient import EventCallback
from dxlclient.client import DxlClient
from dxlclient.client_config import DxlClientConfig
from dxlclient.message import Message, Request, Event

EVENT_REQUEST_TOPIC = "/oc2/cmd"
EVENT_RESPONSE_TOPIC = "/oc2/rsp"
SERVICE_TOPIC = "/oc2"
CONFIG_FILE = ""

config = DxlClientConfig.create_dxl_config_from_file(CONFIG_FILE)

query_features = {
    "headers": {
        "request_id": "abc123",
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "query",
                "target": {
                    "features": [
                        "profiles"
                    ]
                }
            }
        }
    }
}


class OC2EventCallback(EventCallback):
    def on_event(self, rsp_event):
        print("Client received response payload:\n" + str(json.loads(rsp_event.payload)))


with DxlClient(config) as client:
    client.connect()
    # Request Example
    request = Request(SERVICE_TOPIC)
    request.payload = json.dumps(query_features)
    request.other_fields['encoding'] = 'json'
    request.other_fields['contentType'] = 'application/openc2'
    request.other_fields['msgType'] = 'req'
    response = client.sync_request(request)
    if response.message_type != Message.MESSAGE_TYPE_ERROR:
        print("Client received response payload:\n" + str(json.loads(response.payload)))
    # Event Example
    client.add_event_callback(EVENT_RESPONSE_TOPIC, OC2EventCallback())
    event = Event(EVENT_REQUEST_TOPIC)
    event.payload = json.dumps(query_features)
    event.other_fields['encoding'] = 'json'
    event.other_fields['contentType'] = 'application/openc2'
    event.other_fields['msgType'] = 'req'
    client.send_event(event)
    time.sleep(1)

```

*When done with this Producer shell, type exit() and hit enter*

### Check Results
There should be two JSON OpenC2 Response messages, similar to this:
```json
{
    "headers": {
        "request_id": "abc123",
        "created": 1617026741390,
        "to": "Producer1",
        "from": "yuuki"
    },
    "body": {
        "openc2": {
            "response": {
                "status": 200,
                "status_text": "OK - the Command has succeeded.",
                "results": {
                    "profiles": [
                        "slpf",
                        "x-acme"
                    ]
                }
            }
        }
    }
}
```

