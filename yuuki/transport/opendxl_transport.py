from dataclasses import dataclass

from dxlclient.client import DxlClient
from dxlclient.client_config import DxlClientConfig
from dxlclient.callbacks import EventCallback, RequestCallback
from dxlclient.message import Event, Message, Request, Response
from dxlclient.service import ServiceRegistrationInfo

from yuuki import OpenC2RspFields, StatusCode
from yuuki.openc2.openc2_types import OpenC2Headers
from yuuki.transport.consumer import Consumer


@dataclass
class OpenDXLConfig:
    """OpenDXL Configuration to pass to OpenDXL Transport init."""
    EVENT_REQUEST_TOPIC = "/oc2/cmd"
    EVENT_RESPONSE_TOPIC = "/oc2/rsp"
    SERVICE_TOPIC = "/oc2"
    CONFIG_FILE = ""


class OC2EventCallback(EventCallback):
    def __init__(self, client, config, get_response):
        super().__init__()
        self.client = client
        self.config = config
        self.get_response = get_response

    def on_event(self, event):
        encode = event.other_fields.get('encoding', 'json')
        if (event.other_fields.get('msgType') != 'req' or
                event.other_fields.get('contentType') != 'application/openc2'):
            oc2_body = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed Event Fields')
            response = Consumer.make_response_msg(oc2_body, OpenC2Headers(), encode)
        else:
            response = self.get_response(event.payload, encode)

        if response is not None:
            event = Event(self.config.EVENT_RESPONSE_TOPIC)
            event.payload = response
            event.other_fields['encoding'] = encode
            event.other_fields['contentType'] = 'application/openc2'
            event.other_fields['msgType'] = 'rsp'
            self.client.send_event(event)


class OC2RequestCallback(RequestCallback):
    def __init__(self, client, get_response):
        super().__init__()
        self.client = client
        self.get_response = get_response

    def on_request(self, request):
        encode = request.other_fields.get('encoding', 'json')
        if (request.other_fields.get('msgType') != 'req' or
                request.other_fields.get('contentType') != 'application/openc2'):
            oc2_body = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed Request Fields')
            openc2_response = Consumer.make_response_msg(oc2_body, OpenC2Headers(), encode)
        else:
            openc2_response = self.get_response(request.payload, encode)
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
    def __init__(self, cmd_handler, opendxl_config: OpenDXLConfig):
        super().__init__(cmd_handler, opendxl_config)
        self.dxl_client_config = DxlClientConfig.create_dxl_config_from_file(self.transport_config.CONFIG_FILE)

    def start(self):
        with DxlClient(self.dxl_client_config) as client:
            client.connect()
            client.add_event_callback(self.transport_config.EVENT_REQUEST_TOPIC,
                                      OC2EventCallback(client, self.transport_config, self.get_response))
            info = ServiceRegistrationInfo(client, "OC2Service")
            info.add_topic(self.transport_config.SERVICE_TOPIC, OC2RequestCallback(client, self.get_response))
            client.register_service_sync(info, 10)

            while True:
                pass
