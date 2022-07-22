
```
             _____.___.            __   .__ 
             \__  |   |__ __ __ __|  | _|__|
              /   |   |  |  \  |  \  |/ /  |
              \____   |  |  /  |  /    <|  |
              / ______|____/|____/|__|_ \__|
              \/                       \/   
```        

# Table of Contents     

[Introduction](#introduction)  
[Requirements and Setup](#requirements-and-setup)  
[Yuuki's Consumer Components](#components-of-a-yuuki-consumer)  
    * [Consumers](#consumers)  
    * [Actuators](#actuators)  
    * [Serializations](#serializations)  
[Example Consumers](#examples)  
[Transport Functions](#transport-functions)  
    * [HTTP](#HTTP)  
    * [MQTT](#MQTT)  
    * [OpenDXL(experimental)](#opendxl)  
[FAQ](#frequently-asked-questions)
    

## Introduction

Yuuki is a framework for creating OpenC2 Consumers. It serves a few purposes:

* Provide an introduction to OpenC2
* Provide an OpenC2 Consumer for OpenC2 Producers to test against
* Facilitate experimentation with different Actuator profiles, transfer protocols and message serializations

The three main components of Yuuki are the [Consumer](consumers), [Actuator](#actuators), and [Serialization](#serializations) classes, 
defined respectively in the `consumer.py`, `actuator.py`, and `serialization.py` files.

## Requirements and Setup
* Python 3.8+  
* Pip3  
* a Virtual Environments Package (venv in example)  
  
-Create and work on a virtual environment you want to be running Yuuki:  
```
    mkdir yuuki  
    cd yuuki  
    python3 -m venv venv  
    source venv/bin/activate  
```
-Clone Yuuki Repository:  
```
    -git clone **THIS_REPO**  
```
-Create Build folder:   
```
    -python3 -m pip install -U -r requirements.txt  
```    
-Run setup.py for the branch you want:
```
    -python3 setup.py **branch**  
```
-If you plan to use other tools with your actuator, install them:  
```
    -python3 -m pip install **your tools**  
```
-Finally, run an example consumer file. this can be generic and you can add actuators through the command line, 
or you can import them directly in the consumer itself, as shown in this example:   
```
    -python3 examples/mqtt_consumer_full.py  
```


## Components of a Yuuki Consumer

### Consumers  

A Consumer is initialized with a rate limit and a list of OpenC2 language versions that it supports, as well as an optional list of [Actuators](#actuators) and an optional list of [Serializations](#serializations).

```python
from oc2_arch import Consumer

consumer = Consumer(rate_limit=60, versions=['1.0'], actuators=[], serializations=[])
```
  
The Consumer class’s main purpose is to deserialize and process OpenC2 Commands,   
route the Command to the correct Actuator function from the Action-Target pair in the Command,  
and then return a serialized OpenC2 Response based on the results of the Command (if applicable).   
This is accomplished by calling the `process_command` function.  

```python
consumer.process_command(command, 'json')
```

The Consumer class also provides a method to create a serialized Response message.   
This can be run as the result of processing a command, but can also be run by itself.  
You will see it at the end of properly processed command logic, and also  
with many error messages to send the appropriate failure status code as an OpenC2 message.  

```python
from oc2_arch import OpenC2RspFields

consumer.create_response_msg(response_body=OpenC2RspFields(), encode='json')
```
To extend Consumers to support additional Commands and methods of serializing methods, 
the Actuator and Serialization classes are used. Instances of these classes can be provided as arguments to a consumer 
when it is initialized, or can be added later using the `add_actuator_profile` and `add_serialization` methods.


### Actuators

By default, the Consumer class only supports a single Command: `query features`.
The set of Commands supported by the Consumer is extended with Actuators, which can be added to the Consumer either during or after its initialization.

An Actuator is identified by a string representing the namespace identifier (`nsid`) of its Actuator profile.
Actuators consist of a number of action- target pairs, and inherit from the Actuator class, 
giving them access to initialization, pair definition and registration, and some basic error handling.

For example, see the sample implementation of an Actuator based on the [Stateless Packet Filtering](https://docs.oasis-open.org/openc2/oc2slpf/v1.0/oc2slpf-v1.0.html) Actuator profile in `examples/actuators/slpf.py`
[Stateless Packet Filtering](https://docs.oasis-open.org/openc2/oc2slpf/v1.0/oc2slpf-v1.0.html) is a standard Actuator profile with the nsid: `slpf`.
nsids of nonstandard Actuator profiles are prefixed with `x-`.

You can initialize a consumer with one or more Actuators, by importing them into the consumer.
```python
from .actuator import Actuator

example = Actuator(nsid='x-example')
```

After an Actuator is initialized, functions that correspond to Commands that the Actuator supports can also be added to it.
These functions should have an `OpenC2CmdFields` object as their only parameter and return an `OpenC2RspFields` object.

The `pair` decorator is used to indicate to the Actuator which Command a function is intended to support.

```python
from oc2_arch import OpenC2CmdFields, OpenC2RspFields, StatusCode

@example.pair('action', 'target')
def example_command(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    return OpenC2RspFields(status=StatusCode.OK)
```

Functions for Commands that are specified in the Actuator profile, but not implemented by the Actuator should set the `implemented` argument to `False`, and provide a desired response message..
For example, if you are implementing an ipv6 packet filter, which does not have ipv4 functions, but you want to send proper notifications,
changing the implementation of these to False should provide the proper "Command Not Implemented" as opposed to "Actuator Not Found".
```python
@example.pair('action', 'target', implemented=False)
def unsupported_command(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
```


### Serializations

Serialization objects are used to add support for different methods of decoding and encoding messages to the Consumer.
They are initialized with three arguments: the string that will be used to identify the protocol in OpenC2 Messages, 
a function for decoding messages, and a function for encoding messages. 
The Consumer class comes with support for JSON.
```python
import json
from oc2_arch import Serialization

Serialization(name='json', deserialize=json.loads, serialize=json.dumps)
```


## Examples

An example Consumer utilizing different transport protocols, as well as sample Producer scripts have been provided in the `examples` directory.

To demonstrate the OpenC2 Consumer, Yuuki can use its Transport functions to send messages as a basic OpenC2 Producer.
However, if you have another method of sending OpenC2 Commands, Yuuki should work with them as well, with the proper connection info.  
Each Producer sends an OpenC2 Command similar to the following:

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
        "from": "Yuuki"
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

## Transport Functions

Yuuki's Consumer functions require it has OpenC2 to read. Transport functions are how that happens.  
These are found under `/openc2_arch/transports` and have `__init__,` `config` and `transport` functions.  
These were not listed with the other core parts of Yuuki only because they interact with its Consumer logic very little.  
They are very important, but they deal with transporting serialized messages, not OpenC2 Commands.  
This is where your connection info is sent to properly establish connections.  
Tinker with caution!!!  

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
python examples/mqtt_example_full.py --host test.mosquitto.org
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

## Frequently Asked Questions:

#### What is OpenC2?
Open Command and Control, or OpenC2, is an OASIS Technical Committee Specification. 
OpenC2 is a standardized language for the command and control of technologies that provide or support cyber defenses. 
By providing a common language for machine-to-machine communication, OpenC2 is vendor and application agnostic, 
enabling interoperability across a range of cyber security tools and applications.
Learn more about OpenC2 at their website, [openc2.org](https://openc2.org/)

#### Who is "In Charge" of Yuuki?
[OASIS open Projects](https://www.oasis-open.org/open-projects/) operate independently under lightweight rules, 
are funded by sponsorship by organizations committed to the project's success, and are coordinated and managed by OASIS.

#### Where can I find Actuators?
Example Implementations of OASIS approved Actuator Profiles will be provided in the Examples folder. 
Other functions may be in the works, or used for demo purposes, and these do not generally end up on OASIS Main 
until they are fully vetted and polished. However, if you want to see what we're cooking up, feel free to [take a look](https://github.com/ScreamBun/openc2-yuuki/tree/develop)

#### Can I make my own Actuators for Yuuki?
Yes! Yuuki is an Open Project, and while OASIS requires contributors to 
read and agree to their Contributor Licensing Agreement, absolutely anyone can pull down
and play around with the code. You can have Yuuki perform officially approved 
OpenC2 Actuator Profile functions, or just mess around with things of your own design.
Good Luck, and Have Fun!