#!/usr/bin/env python3

import ssl
import paho.mqtt.publish as publish
import mqtt_config as config
import json

login = {'username': config.user_name, 'password': config.user_pw}

query_features = {
    "headers": {
        "request_id": "95ad511c-3339-4111-9c47-9156c47d37d3",
        "created": 1595268027000,
        "from": "Producer1@example.com",
        "to": ["consumer1@example.com", "consumer2@example.com", "consumer3@example.com"]
    },
    "body": {
        "openc2": {
            "request": {
                "action": "deny",
                "target": {
                    "ipv4_connection": {"src_port": "http://www.example.com"}}}}}}

as_json = json.dumps(query_features)

header_bytes = bytes.fromhex('9001')
# serialized_msg = header_bytes + bytes(serialized_msg, 'utf-8')

# my_byte_header = b'\t\x00\x00\x00'
# print(my_byte_header)
as_json = header_bytes + bytes(as_json, 'utf-8')
print(as_json)

publish.single(config.YOUR_NAME_PREFIX + "oc2/cmd", payload=as_json, qos=0,
               retain=False, hostname=config.broker_ip, port=config.broker_port, client_id="",
               keepalive=60, will=None, auth=login, tls=None)
