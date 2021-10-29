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
from flask import Flask, request, make_response
from werkzeug.http import parse_options_header

from .http_config import HttpConfig
from .consumer import Consumer
from .openc2_types import StatusCode, OpenC2Headers, OpenC2RspFields


class Http(Consumer):
    """Implements Transport base class for HTTP"""

    def __init__(self, cmd_handler, http_config: HttpConfig):
        super().__init__(cmd_handler, http_config)
        self.app = Flask('yuuki')
        self.setup(self.app)

    def setup(self, app):
        @app.route('/', methods=['POST'])
        def receive():
            try:
                encode = self.verify_headers(request.headers)
            except ValueError:
                encode = 'json'
                oc2_body = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed HTTP Request')
                response = self.make_response_msg(oc2_body, OpenC2Headers(), encode)
            else:
                response = self.get_response(request.get_data(), encode)

            if response is not None:
                http_response = make_response(response)
                http_response.content_type = f'application/openc2-rsp+{encode};version=1.0'
                return http_response
            else:
                return '', 204

    def start(self):
        if self.config.authentication.enable:
            self.app.run(port=self.config.port, host=self.config.host,
                         certfile=self.config.authentication.certfile,
                         keyfile=self.config.authentication.keyfile,
                         ca_certs=self.config.authentication.ca_certs)
        else:
            self.app.run(port=self.config.port, host=self.config.host)

    @staticmethod
    def verify_headers(headers):
        if 'Host' and 'Content-type' in headers:
            try:
                encode = parse_options_header(headers['Content-type'])[0].split('/')[1].split('+')[1]
            except IndexError as error:
                raise ValueError('Invalid OpenC2 HTTP Headers') from error
            if headers['Content-type'] == f"application/openc2-cmd+{encode};version=1.0":
                return encode
        raise ValueError('Invalid OpenC2 HTTP Headers')
