#!/usr/bin/env python3

import ssl
import paho.mqtt.client as mqtt
import mqtt_config as config


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(config.YOUR_NAME_PREFIX + "oc2/rsp")


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


client = mqtt.Client()
client.username_pw_set(config.user_name, password=config.user_pw)
client.on_connect = on_connect
client.on_message = on_message

# Using TLS? Insert context code here

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
# client.tls_set_context(context)

client.connect(config.broker_ip, config.broker_port, 60)

client.loop_forever()
