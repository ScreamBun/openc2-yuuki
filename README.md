# Introduction

Yuuki is a lightweight OpenC2 framework that comes with example Consumers, all built on an extensible library, with default support for **HTTP** and **MQTT** protocols. It serves a few purposes:

* Provide [ready-made examples](#simple-example-http) to
  * Introduce you to OpenC2
  * Test against your own OpenC2 Producer
* Provide a library to
  * Ease implementation of Actuator Profiles
  * Ease experimentation with different Transports, Serializations and Validators

To jump right in, head over to the examples directory, or follow along below for a guided tour.

# Closed Issues

* [x] Support HTTP Transport
* [x] Support MQTT Transport
* [x] Support JSON serialization
* [x] Allow swapping in new serializations
* [x] Allow swapping in new transports
* [x] Allow swapping in new validation
* [x] Support TLS
* [x] Support Running Multiple Actuator Profiles At Once

# Open Issues

* [ ] None! Please open a new issue! 

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

For example, look at how the main OpenC2 Consumer is contructed in **simple_http.py** in the *examples* folder:

```python
consumer = Consumer( 
    cmd_handler   = CmdHandler(validator = validate_and_convert),
    transport     = Http(http_config),
    serialization = Json )
```

See the **Json**, **Http** and **validate_and_convert** arguments? Simply replace any of those with a library of your own; just as long as you follow the same Yuuki interface.

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

# Simple Example: HTTP

Running HTTP locally shouldn't require any configuration. Run the HTTP consumer `simple_http.py` in the *examples* directory with

```sh
python simple_http.py
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
import requests
import json

query_features = {
        "action": "query",
        "target": {
            "features": ["versions","profiles"]
        },
        "args": {
            "response_requested": "complete"
        }
    }

as_json = json.dumps(query_features)
headers = {"Content-Type" : "application/openc2-cmd+json;version=1.0"}

response = requests.post("http://127.0.0.1:9001", json=as_json, headers=headers, verify=False)

print('Sent OpenC2 Command')
print(json.dumps(response.json(), indent=4))
pass
```

Because we're testing locally, you should instantly see the OpenC2 Response, similar to this.

```json
{
    "status": 200,
    "status_text": "OK - the Command has succeeded.",
    "results": {
        "versions": [
            "1.0"
        ],
        "profiles": [
            "slpf"
        ]
    }
}
```

*When done with this Producer shell, type exit() and hit enter*

Success! The Yuuki Consumer successfully received an OpenC2 Command, then returned an Openc2 Response.

### Shut Down
In the Yuuki Consumer shell, hit CTRL-C to stop the process.

# Advanced Example: MQTT
MQTT requires a little configuration. We'll need to connect to an MQTT broker. Mosquitto is a free broker that's always up (and offers no privacy).

At the bottom of `advanced_mqtt.py` in the *examples* directory, supply the socket address for the broker.

```python
    mqtt_config = MqttConfig(
                    broker=BrokerConfig(
                        socket='test.mosquitto.org:1883'))
```

Save your file and start the advanced example:

```sh
python advanced_mqtt.py
```

That's it! Your OpenC2 MQTT Consumer is ready for any published commands. If you're familiar with MQTT, by default Yuuki listens for OpenC2 commands on the topic **yuuki_user/oc2/cmd**, and publishes its responses to **yuuki_user/oc2/rsp**. Next, we'll write some quick scripts to make sure it's working.

If you'd like to change the topics, you can like so:

```python
    mqtt_config = MqttConfig(
                    ...
                    subscriptions=[Subscription('subcribe/to/command/topic', 1),
                                   Subscription('another/command/topic', 0)],
                    publishes=[Publish('publish/responses/here', 0),
                               Publish('another/response/topic', 3)])
```

## Test MQTT Transport

### Subscribe to OpenC2 Responses
In a new terminal window, go back to the root "yuuki" folder, then enable the virtual environment and start a Python shell.

```sh
source venv/bin/activate
python
```

Copy this text into the shell.

```python
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print("Connected to broker. Result:", str(rc))
    topic_filter = "yuuki_user/oc2/rsp"
    client.subscribe(topic_filter)
    print("Listening for OpenC2 responses on", topic_filter)

def on_message(client, userdata, msg):
    print("MESSAGE FROM TOPIC {} START:".format(msg.topic))
    print(json.dumps(json.loads(msg.payload), indent=4))
    print("MESSAGE END.\n")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("test.mosquitto.org", 1883, 60)
client.loop_forever()
pass

```

*Later, when done with this shell, hit CTRL-C, then type exit() and hit enter*

### Publish an OpenC2 Command
In _yet_ _another_ terminal window, enable the virtual environment and start a Python shell.

```sh
source venv/bin/activate
python
```

Copy this text into the shell.

```python
import paho.mqtt.publish as publish
import json

query_features = {
        "action": "query",
        "target": {
            "features": ["pairs", "versions"]
        },
        "args": {
            "response_requested": "complete"
        }
    }

as_json = json.dumps(query_features)

publish.single("yuuki_user/oc2/cmd", payload=as_json, hostname="test.mosquitto.org", port=1883)
pass

```

*Later, when done with this shell, type exit() and hit enter*

### Check Results
Go back to the previous subscription shell, and there should be a JSON OpenC2 response message, similiar to this:
```json
{
    "status": 200,
    "status_text": "OK - the Command has succeeded.",
    "results": {
        "versions": [
            "1.0"
        ],
        "pairs": [
            "slpf"
        ]
    }
}
```

Success! The Yuuki Consumer successfully received an OpenC2 Command, then published an Openc2 Response.

