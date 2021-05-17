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

from werkzeug.http import parse_options_header, parse_accept_header
from quart import (
    Quart,
    request,
    make_response
)

from .oc2_base import Transport

from ..openc2.oc2_types import StatusCode, OC2Rsp, OC2Headers
from ..serialization import serializations


@dataclass
class HttpConfig:
    """Simple Http Configuration to pass to Http Transport init."""

    consumer_socket: str = '127.0.0.1:9001'
    use_tls: bool = False
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    ca_certs: Optional[str] = None


class Http(Transport):
    """Implements Transport base class for HTTP"""

    def __init__(self, http_config: HttpConfig):
        super().__init__(http_config)
        self.app = Quart(__name__)
        self.setup(self.app)

    def process_config(self):
        self.host, port = self.config.consumer_socket.split(':')
        self.port = int(port)

        if self.config.use_tls:
            if self.config.certfile is None or self.config.keyfile is None:
                raise ValueError('TLS requires a keyfile and certfile.')

    def setup(self, app):
        @app.route('/', methods=['POST'])
        async def receive():
            decode, encode, request_id, date = self.verify_headers(request.headers)
            if decode and encode:
                formats = set(encode).intersection(serializations)
                if formats:
                    raw_data = await request.get_data()
                    oc2_msg = await self.get_response(raw_data, (decode, formats.pop()),
                                                      request_id=request_id, date=date, http=True)
                else:
                    oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST, status_text='Unsupported serialization format')
                    oc2_msg = self.make_response_msg(oc2_body, OC2Headers(), 'json')
            else:
                oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST, status_text='Malformed HTTP Request')
                oc2_msg = self.make_response_msg(oc2_body, OC2Headers(), encode if encode else 'json')

            http_response = await make_response(oc2_msg)
            http_response.content_type = 'application/openc2-rsp+json;version=1.0'
            return http_response

    def start(self):
        if self.config.use_tls:
            self.app.run(port=self.port, host=self.host,
                         certfile=self.config.certfile,
                         keyfile=self.config.keyfile,
                         ca_certs=self.config.ca_certs)
        else:
            self.app.run(port=self.port, host=self.host)

    @staticmethod
    def verify_headers(headers):
        decode = None
        encode = None
        if 'Host' and 'Content-type' in headers:
            try:
                decode = parse_options_header(headers['Content-type'])[0].split('/')[1].split('+')[1]
                if not headers['Content-type'] == f'application/openc2-cmd+{decode};version=1.0':
                    decode = None
            except IndexError:
                decode = None
        if 'Accept' in headers:
            try:
                encode = [x[0].split('/')[1].split('+')[1].split(';')[0] for x in parse_accept_header(headers['Accept'])]
                if not headers['Accept'] == ', '.join(f'application/openc2-rsp+{x};version=1.0' for x in encode):
                    encode = None
            except IndexError:
                encode = None
        date = headers['Date'] if 'Date' in headers else None
        request_id = headers['X-Request-ID'] if 'X-Request-ID' in headers else None
        return decode, encode, request_id, date
