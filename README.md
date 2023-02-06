
<a href="https://openc2.org/" target="_blank">![OpenC2](https://github.com/ScreamBun/SB_Utils/blob/master/assets/images/openc2.png?raw=true)</a>

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-yellow)](https://www.python.org/downloads/release/python-3100/) 
[![Open2C Lang Spec](https://img.shields.io/badge/Open2C%20Lang%20Spec-1.0-brightgreen)](https://openc2.org/specifications)

## Table of Contents  
  
- [Introduction](#introduction)  
- [Requirements and Setup](#requirements-and-setup)  
- [Yuuki's Consumer Components](#components-of-a-yuuki-consumer)  
  - [Consumers](#consumers)  
  - [Actuators](#actuators)  
  - [Serializations](#serializations)  
- [Example Consumers](#examples)  
- [Transport Functions](#transport-functions)  
  - [HTTP](#HTTP)  
  - [MQTT](#MQTT)   
- [FAQ](#frequently-asked-questions)
    

## Introduction
Yuuki is a tool for creating OpenC2 Consumers.
Open Command and Control, or OpenC2, is a standardized language for the command and control of technologies that provide or support cyber defenses.
OpenC2 Commands are sent by Producer devices to Consumers that receive and implement Commands.  
OpenC2 is defined in the [OpenC2 Architecture Specification](https://docs.oasis-open.org/openc2/oc2arch/v1.0/csd02/oc2arch-v1.0-csd02.md) and [OpenC2 Language Specification](https://github.com/oasis-tcs/openc2-oc2ls/blob/published/oc2ls-v1.0-cs02.md).

### Background

This GitHub public repository ( [https://github.com/oasis-open/openc2-yuuki](https://github.com/oasis-open/openc2-yuuki) ) was created at the request of the [OASIS Open Command and Control (OpenC2) TC](https://www.oasis-open.org/committees/openc2/) as an [OASIS TC Open Repository](https://www.oasis-open.org/resources/open-repositories/) to support development of open source resources related to Technical Committee work.

While this TC Open Repository remains associated with the sponsor TC, its development priorities, leadership, intellectual property terms, participation rules, and other matters of governance are [separate and distinct](https://github.com/oasis-open/openc2-yuuki/blob/master/CONTRIBUTING.md#governance-distinct-from-oasis-tc-process) from the OASIS TC Process and related policies.

All contributions made to this TC Open Repository are subject to open source license terms expressed in the [BSD-3-Clause License](https://www.oasis-open.org/sites/www.oasis-open.org/files/BSD-3-Clause.txt).  That license was selected as the declared ["Applicable License"](https://www.oasis-open.org/resources/open-repositories/licenses) when the TC Open Repository was created.

As documented in ["Public Participation Invited"](https://github.com/oasis-open/openc2-yuuki/blob/master/CONTRIBUTING.md#public-participation-invited), contributions to this OASIS TC Open Repository are invited from all parties, whether affiliated with OASIS or not.  Participants must have a GitHub account, but no fees or OASIS membership obligations are required. Participation is expected to be consistent with the [OASIS TC Open Repository Guidelines and Procedures](https://www.oasis-open.org/policies-guidelines/open-repositories), the open source [LICENSE](https://github.com/oasis-open/openc2-yuuki/blob/master/LICENSE) designated for this particular repository, and the requirement for an [Individual Contributor License Agreement](https://www.oasis-open.org/resources/open-repositories/cla/individual-cla) that governs intellectual property.
  

### Statement of Purpose
Statement of Purpose for this OASIS TC Open Repository (openc2-yuuki) as [proposed](https://drive.google.com/open?id=0B-FunCZrr-vtcUJTWVBNaFNlVUE) and [approved](https://www.oasis-open.org/committees/ballot.php?id=3115) [[bis]](https://issues.oasis-open.org/browse/TCADMIN-2746) by the OpenC2 TC:  
The purpose of the openc2-yuuki GitHub repository is to   
    (a) demonstrate the implementation of OpenC2 via multiple dispatch on type, and    
    (b) provision a codebase to enable other prototype efforts.    
The initial codebase for the openc2-yuuki repository is imported from the OpenC2 Forum's Github repository.  

Yuuki is designed to be a good introduction to OpenC2, to facilitate experimentation with different Actuator profiles, transfer protocols, and message serializations, and to provide a simple OpenC2 Consumer for OpenC2 Producers to test against.  

The three main components of Yuuki are the [Consumer](consumers), [Actuator](#actuators), and [Serialization](#serializations) classes, 
defined respectively in the `consumer.py`, `actuator.py`, and `serialization.py` files.

## Requirements and Setup
* [Python 3.8+](https://www.python.org/downloads/)   
* [Pip3](https://pip.pypa.io/en/stable/) - Package Installer for Python
* a Virtual Environments Package (venv in example)  
  
Create and work on a virtual environment you want to be running Yuuki:  
```
    mkdir yuuki  
    cd yuuki  
    python3 -m venv venv  
    source venv/bin/activate  
```
Clone Yuuki Repository:  
```
    -git clone **THIS_REPO**  
```
Create Build folder:   
```
    -python3 -m pip install -U -r requirements.txt  
```    
Run setup.py for the branch you want:
```
    -python3 setup.py **branch**  
```
If you plan to use other tools with your actuator, install them:  
```
    -python3 -m pip install **your tools**  
```
Finally, run an example consumer file. this can be generic and you can add actuators through the command line, 
or you can import them directly in the consumer itself, as shown in this example:   
```
    -python3 examples/mqtt_consumer_full.py  
```


## Components of a Yuuki Consumer

### Consumers  

A Consumer is initialized with a rate limit and a list of OpenC2 language versions that it supports,  
as well as an optional list of [Actuators](#actuators) and an optional list of [Serializations](#serializations).
Although more complicated than adding them on initialization, Actuators and Serializations may be added later using the Command Line Interface.  
Being focused on cyber defense, Yuuki Consumers have a rate limit that caps the maximum amount of commands they can receive in a minute.
This helps protect against network overload, recursion errors, or other unforseen issues. 

```python
from yuuki import Consumer

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
from yuuki import OpenC2RspFields

consumer.create_response_msg(response_body=OpenC2RspFields(), encode='json')
```
To extend Consumers to support additional Commands and methods of serializing methods, 
the Actuator and Serialization classes are used. Instances of these classes can be provided as arguments to a Consumer 
when it is initialized, or can be added later using the `add_actuator_profile` and `add_serialization` methods.


### Actuators

By default, the Consumer class only supports a single Command: `query features`.
The set of Commands supported by the Consumer is extended with Actuators, which can be added to the Consumer either during or after its initialization.

An Actuator is identified by a string representing the namespace identifier (`nsid`) of its Actuator profile.
Actuators consist of a number of action- target pairs, and inherit from the Actuator class, 
giving them access to initialization, pair definition and registration, and some basic error handling.

For example, see the sample implementation of an Actuator based on the [Stateless Packet Filtering](https://docs.oasis-open.org/openc2/oc2slpf/v1.0/oc2slpf-v1.0.html) Actuator profile in `examples/actuators/slpf.py`.
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
Pairs consist of an action and a target the actuator will read from the OpenC2 Command, as well as logic for what actions to perform and OpenC2 Response to generate.  


```python
from yuuki import OpenC2CmdFields, OpenC2RspFields, StatusCode

@example.pair('action', 'target')
def example_command(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    return OpenC2RspFields(status=StatusCode.OK)
```

Functions for Commands that are specified in the Actuator profile, but not implemented by the Actuator should set the `implemented` argument to `False`, and provide a desired response message.  
For example, if you are implementing an IPv6 packet filter, which does not have IPv4 functions, but you want to send proper notifications,
changing the implementation of these to False should provide the proper `Unimplemented Command` as opposed to `Actuator Not Found`.
```python
@example.pair('action', 'target', implemented=False)
def unsupported_command(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
```


### Serializations

Serialization objects add support for different message encoding and decoding methods to the Consumer.  
They are initialized with three arguments: a string to identify the protocol in OpenC2 Messages,  
a function for encoding messages, and a function for decoding messages.  
The Consumer class comes with support for JSON.
```python
import json
from yuuki import Serialization

Serialization(name='json', deserialize=json.loads, serialize=json.dumps)
```


## Examples

An example Consumer utilizing different transport protocols, as well as sample Producer scripts are provided in the `examples` directory.

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
This is where your connection info is sent to properly establish connections, so tinker with caution!  

### MQTT
You can find the OpenC2 MQTT Transfer Specification [Here](https://github.com/oasis-tcs/openc2-transf-mqtt/blob/published/transf-mqtt-v1.0-cs01.md).
A connection to an MQTT broker is required. A publicly available MQTT broker is hosted at [test.mosquitto.org](https://test.mosquitto.org).

#### Start Consumer:
```sh
python examples/mqtt_example_full.py --host test.mosquitto.org
```

#### Publish an OpenC2 Command:
```sh
python producers/mqtt_producer.py --host test.mosquitto.org
```

### HTTP
You can find the OpenC2 HTTPS Transfer Specification [Here](https://github.com/oasis-tcs/openc2-impl-https/blob/published/open-impl-https-v1.1-cs01.md)

#### Start Consumer:
```sh
python examples/http_example.py
```

#### Publish an OpenC2 Command:
```sh
python examples/producers/http_producer.py
```

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
  
#### Where can I find Actuators?  
Example Implementations of OASIS approved Actuator Profiles will be provided in the Examples folder. 
Other functions may be in the works, or used for demo purposes, and these do not generally end up on OASIS Main 
until they are fully vetted and polished. However, if you want to see what we're cooking up, feel free to [take a look](https://github.com/ScreamBun/openc2-yuuki/tree/develop)
  
#### Can I make my own Actuators for Yuuki?
Yes! Yuuki is an [OASIS Open Project](https://www.oasis-open.org/open-projects/), and while OASIS requires contributors to 
read and agree to their Contributor Licensing Agreement, absolutely anyone can pull down
and play around with the code. You can have Yuuki perform officially approved 
OpenC2 Actuator Profile functions, or just mess around with things of your own design.
Good Luck, and Have Fun!

#### Who Maintains Yuuki?
TC Open Repository [Maintainers](https://www.oasis-open.org/resources/open-repositories/maintainers-guide) are responsible for oversight of this project's community development activities, including evaluation of GitHub [pull requests]() and [preserving](https://www.oasis-open.org/policies-guidelines/open-repositories#repositoryManagement) open source principles of openness and fairness. Maintainers are recognized and trusted experts who serve to implement community goals and consensus design preferences.
Initially, the associated TC members have designated one or more persons to serve as Maintainer(s); subsequently, participating community members may select additional or substitute Maintainers, per [consensus agreements](https://www.oasis-open.org/maintainers-guide/#additionalMaintainers).
Current Maintainers of this TC Open Repository  

* [David Lemire](mailto:david.lemire@hii-tsd.com); Email: david.lemire@hii-tsd.com 
* The ScreamingBunny Development team; GitHub ID: [https://github.com/ScreamBun](https://github.com/ScreamBun)

#### Where can I learn about OASIS TC Open Repositories?
* [TC Open Repositories: Overview and Resources](https://www.oasis-open.org/resources/open-repositories/)
* [Frequently Asked Questions](https://www.oasis-open.org/resources/open-repositories/faq)
* [Open Source Licenses](https://www.oasis-open.org/resources/open-repositories/licenses)
* [Contributor License Agreements (CLAs)](https://www.oasis-open.org/resources/open-repositories/cla)
* [Maintainers' Guidelines and Agreement](https://www.oasis-open.org/resources/open-repositories/maintainers-guide)

#### How do I submit Feedback to this Repository?
Questions or comments about this TC Open Repository's activities should be composed as GitHub issues or comments. If use of an issue/comment is not possible or appropriate, questions may be directed by email to the Maintainer(s) [listed above](https://ccoe-gitlab.hii-tsd.com/screamingbunny/yuuki/-/blob/34630146e94b73b0604bdeea80b74339607e08e3/README.md#currentMaintainers).  Please send general questions about TC Open Repository participation to OASIS Staff at [repository-admin@oasis-open.org](mailto:repository-admin@oasis-open.org) and any specific CLA-related questions to [repository-cla@oasis-open.org](mailto:repository-cla@oasis-open.org).

TEST