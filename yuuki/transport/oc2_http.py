"""
HTTP Transport

Contains the transport class to instantiate, and its config to customize.

This tranport receives messages, then sends them on to a handler,
and awaits a response to send back.

Use as an argument to a Consumer constructor, eg:

http_config = HttpConfig(consumer_socket=...)
http_transport = Http(http_config)
my_openc2_consumer = Consumer(transport=http_transport, ...)
my_openc2_consumer.start()

"""
from dataclasses import dataclass
from typing import Optional

import werkzeug
from quart import (
    Quart,
    request,
    make_response
)

from .oc2_base import Consumer

from ..openc2.oc2_types import StatusCode, OC2Rsp, OC2Headers


@dataclass
class HttpConfig:
    """Http Configuration to pass to Http Transport init."""

    consumer_socket: str = '127.0.0.1:9001'
    use_tls: bool = False
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    ca_certs: Optional[str] = None


class Http(Consumer):
    """Implements Transport base class for HTTP"""

    def __init__(self, cmd_handler, http_config: HttpConfig):
        super().__init__(cmd_handler, http_config)
        self.app = Quart(__name__)
        self.setup(self.app)
        self.host, port = self.transport_config.consumer_socket.split(':')
        self.port = int(port)
        if self.transport_config.use_tls:
            if self.transport_config.certfile is None or self.transport_config.keyfile is None:
                raise ValueError('TLS requires a keyfile and certfile.')

    def setup(self, app):
        @app.route('/', methods=['POST'])
        async def receive():
            encode = self.verify_headers(request.headers)
            if encode:
                raw_data = await request.get_data()
                oc2_msg = await self.get_response(raw_data, encode)
            else:
                oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST, status_text='Malformed HTTP Request')
                oc2_msg = self.make_response_msg(oc2_body, OC2Headers(), encode)

            http_response = await make_response(oc2_msg)
            http_response.content_type = 'application/openc2-rsp+json;version=1.0'
            return http_response

    def start(self):
        if self.transport_config.use_tls:
            self.app.run(port=self.port, host=self.host,
                         certfile=self.transport_config.certfile,
                         keyfile=self.transport_config.keyfile,
                         ca_certs=self.transport_config.ca_certs)
        else:
            self.app.run(port=self.port, host=self.host)

    @staticmethod
    def verify_headers(headers):
        if 'Host' and 'Content-type' in headers:
            try:
                encode = werkzeug.http.parse_options_header(headers['Content-type'])[0].split('/')[1].split('+')[1]
            except IndexError:
                return None
            if headers['Content-type'] == f"application/openc2-cmd+{encode};version=1.0":
                return encode
        return None
