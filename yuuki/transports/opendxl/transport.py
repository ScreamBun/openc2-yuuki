"""OpenDXL Consumer
"""

from typing import List

from dxlclient.client import DxlClient
from dxlclient.client_config import DxlClientConfig
from dxlclient.callbacks import EventCallback, RequestCallback
from dxlclient.message import Event, Request, Response
from dxlclient.service import ServiceRegistrationInfo

from yuuki.consumer import Consumer
from yuuki.openc2_types import OpenC2Headers, OpenC2RspFields, StatusCode
from yuuki.actuator import Actuator
from yuuki.serialization import Serialization
from .config import OpenDXLConfig


class OC2EventCallback(EventCallback):
    """Handles received OpenDXL Events"""
    def __init__(self, client, config, consumer):
        super().__init__()
        self.client = client
        self.config = config
        self.consumer = consumer

    def on_event(self, event: Event):
        encode = event.other_fields.get('encoding', 'json')
        if (event.other_fields.get('msgType') != 'req' or
                event.other_fields.get('contentType') != 'application/openc2'):
            oc2_body = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed Event Fields')
            response = self.consumer.create_response_msg(oc2_body, OpenC2Headers(), encode)
        else:
            response = self.consumer.process_command(event.payload, encode)

        if response is not None:
            event = Event(self.config.event_response_topic)
            event.payload = response
            event.other_fields['encoding'] = encode
            event.other_fields['contentType'] = 'application/openc2'
            event.other_fields['msgType'] = 'rsp'
            self.client.send_event(event)


class OC2RequestCallback(RequestCallback):
    """Handles received OpenDXL Requests"""
    def __init__(self, client, consumer):
        super().__init__()
        self.client = client
        self.consumer = consumer

    def on_request(self, request: Request):
        encode = request.other_fields.get('encoding', 'json')
        if (request.other_fields.get('msgType') != 'req' or
                request.other_fields.get('contentType') != 'application/openc2'):
            oc2_body = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed Request Fields')
            openc2_response = self.consumer.create_response_msg(oc2_body, OpenC2Headers(), encode)
        else:
            openc2_response = self.consumer.process_command(request.payload, encode)
        opendxl_response = Response(request)
        if openc2_response is not None:
            opendxl_response.payload = openc2_response
            opendxl_response.other_fields['encoding'] = encode
            opendxl_response.other_fields['contentType'] = 'application/openc2'
            opendxl_response.other_fields['msgType'] = 'rsp'
        else:
            opendxl_response.payload = ''
        self.client.send_response(opendxl_response)


class OpenDxl(Consumer):
    """Implements transport functionality for OpenDXL"""

    def __init__(
            self,
            rate_limit: int,
            versions: List[str],
            opendxl_config: OpenDXLConfig,
            actuators: List[Actuator] = None,
            serializations: List[Serialization] = None
    ):
        super().__init__(rate_limit, versions, opendxl_config, actuators, serializations)
        self.dxl_client_config = DxlClientConfig.create_dxl_config_from_file(self.config.config_file)

    def start(self):
        with DxlClient(self.dxl_client_config) as client:
            client.connect()
            client.add_event_callback(self.config.event_request_topic, OC2EventCallback(client, self.config, self))
            info = ServiceRegistrationInfo(client, "OC2Service")
            info.add_topic(self.config.service_topic, OC2RequestCallback(client, self))
            client.register_service_sync(info, 10)

            while True:
                pass
