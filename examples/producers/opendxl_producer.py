import time
import json
import argparse

from dxlclient import EventCallback
from dxlclient.client import DxlClient
from dxlclient.client_config import DxlClientConfig
from dxlclient.message import Message, Request, Event

import openc2_command


event_request_topic = "oc2/cmd"
event_response_topic = "oc2/rsp"
service_topic = "oc2"

parser = argparse.ArgumentParser(description="OpenDXL Producer")
parser.add_argument("config_file", help="OpenDXL configuration file")
args = parser.parse_args()

config = DxlClientConfig.create_dxl_config_from_file(args.config_file)


class OC2EventCallback(EventCallback):
    def on_event(self, rsp_event):
        print("Event Response:")
        print(json.dumps(json.loads(rsp_event.payload), indent=4))


with DxlClient(config) as client:
    client.connect()
    # Request Example
    request = Request(service_topic)
    request.payload = json.dumps(openc2_command.query_features)
    request.other_fields['encoding'] = 'json'
    request.other_fields['contentType'] = 'application/openc2'
    request.other_fields['msgType'] = 'req'
    response = client.sync_request(request, timeout=5)
    if response.message_type != Message.MESSAGE_TYPE_ERROR:
        print("Request Response:")
        print(json.dumps(json.loads(response.payload), indent=4))
    # Event Example
    client.add_event_callback(event_response_topic, OC2EventCallback())
    event = Event(event_request_topic)
    event.payload = json.dumps(openc2_command.query_features)
    event.other_fields['encoding'] = 'json'
    event.other_fields['contentType'] = 'application/openc2'
    event.other_fields['msgType'] = 'req'
    client.send_event(event)
    time.sleep(1)
