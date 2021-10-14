import json
import time
from typing import Union
import subprocess

import pytest
import cbor2

from paho.mqtt import client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.subscribeoptions import SubscribeOptions


@pytest.fixture(scope="module", autouse=True)
def start_yuuki(request):
    proc = subprocess.Popen(["python", "yuuki/tests/mqtt_example.py"])
    time.sleep(3)
    request.addfinalizer(proc.kill)


response: Union[str, bytes, None] = None


def on_message(client, userdata, msg):
    global response
    response = msg.payload


@pytest.fixture(scope="class")
def mqtt_client():
    mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
    mqtt_client.on_message = on_message
    mqtt_client.connect(host="test.mosquitto.org", port=1883, keepalive=60, clean_start=False)
    mqtt_client.subscribe(topic="oc2/rsp",
                          options=SubscribeOptions(qos=1, noLocal=True, retainAsPublished=True, retainHandling=0))
    yield mqtt_client
    mqtt_client.disconnect()


@pytest.fixture(scope="function")
def oc2_properties():
    oc2_properties = Properties(PacketTypes.PUBLISH)
    oc2_properties.PayloadFormatIndicator = 1
    oc2_properties.ContentType = "application/openc2"
    return oc2_properties


@pytest.mark.parametrize("data_format, encode, decode", [
    ("json", json.dumps, json.loads),
    ("cbor", cbor2.dumps, cbor2.loads)
])
class TestMQTT:
    def test_query(self, data_format, encode, decode, query_features, expected_response, mqtt_client, oc2_properties):
        global response
        oc2_properties.UserProperty = [("msgType", "req"), ("encoding", data_format)]
        mqtt_client.publish(topic="oc2/cmd", payload=encode(query_features),
                            qos=1, retain=False, properties=oc2_properties)
        mqtt_client.loop_start()
        while response is None:
            time.sleep(.1)
        mqtt_client.loop_stop()

        expected_response['headers'].pop('created')
        actual_response = decode(response)
        actual_response['headers'].pop('created')

        assert expected_response == actual_response

        response = None
