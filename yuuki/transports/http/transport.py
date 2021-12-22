"""HTTP Consumer
https://docs.oasis-open.org/openc2/open-impl-https/v1.0/open-impl-https-v1.0.html
"""
import logging
from typing import List

from flask import Flask, request, make_response
from werkzeug.http import parse_options_header

from .config import HttpConfig
from yuuki.consumer import Consumer
from yuuki.openc2_types import StatusCode, OpenC2Headers, OpenC2RspFields
from yuuki.actuator import Actuator
from yuuki.serialization import Serialization


class Http(Consumer):
    """Implements transport functionality for HTTP"""

    def __init__(
            self,
            rate_limit: int,
            versions: List[str],
            http_config: HttpConfig,
            actuators: List[Actuator] = None,
            serializations: List[Serialization] = None
    ):
        super().__init__(rate_limit, versions, http_config, actuators, serializations)
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
                response = self.create_response_msg(oc2_body, OpenC2Headers(), encode)
            else:
                response = self.process_command(request.get_data(), encode)

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
        """
        Verifies that the HTTP headers for the received OpenC2 command are valid, and parses the message serialization
        format from the headers

        :param headers: HTTP headers from received OpenC2 Command.

        :return: String specifying the serialization format of the received OpenC2 Command.
        """
        logging.debug(f'Message Headers:\n{headers}')
        if 'Host' and 'Content-type' in headers:
            try:
                encode = parse_options_header(headers['Content-type'])[0].split('/')[1].split('+')[1]
            except IndexError as error:
                raise ValueError('Invalid OpenC2 HTTP Headers') from error
            if headers['Content-type'] == f'application/openc2-cmd+{encode};version=1.0':
                return encode
        raise ValueError('Invalid OpenC2 HTTP Headers')
