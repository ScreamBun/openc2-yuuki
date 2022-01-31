import json
import argparse

from paho.mqtt import client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.subscribeoptions import SubscribeOptions

import openc2_command


parser = argparse.ArgumentParser(description="MQTT Producer")
parser.add_argument("--host", help="MQTT Broker host")
parser.add_argument("--port", type=int, help="MQTT Broker port")
args = parser.parse_args()

host = args.host if args.host is not None else "127.0.0.1"
port = args.port if args.port is not None else 1883

oc2_properties = Properties(PacketTypes.PUBLISH)
oc2_properties.PayloadFormatIndicator = 1
oc2_properties.ContentType = "application/openc2"
oc2_properties.UserProperty = [("msgType", "req"), ("encoding", "json")]


def on_message(client, userdata, msg):
    print(json.dumps(json.loads(msg.payload), indent=4))
    client.disconnect()


mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
mqtt_client.on_message = on_message
mqtt_client.connect(host=host, port=port, keepalive=60, clean_start=False)
mqtt_client.subscribe(topic="oc2/rsp",
                      options=SubscribeOptions(qos=1, noLocal=True, retainAsPublished=True, retainHandling=0))
mqtt_client.publish(topic="oc2/cmd", payload=json.dumps(openc2_command.query_features),
                    qos=1, retain=False, properties=oc2_properties)
mqtt_client.loop_forever()
