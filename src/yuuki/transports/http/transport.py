"""
HTTP Consumer
https://docs.oasis-open.org/openc2/open-impl-https/v1.0/open-impl-https-v1.0.html
"""
import logging

from flask import Flask, request, make_response
from werkzeug.http import parse_options_header
from waitress import serve
from .config import HttpConfig
from ...consumer import Consumer
from ...openc2_types import StatusCode, OpenC2RspFields


class HttpTransport:
    """
    Implements transport functionality for HTTP
    """
    consumer: Consumer
    config: HttpConfig
    app: Flask

    def __init__(self, consumer: Consumer, config: HttpConfig):
        self.consumer = consumer
        self.config = config
        self.app = Flask('oc2_arch')
        self.app.add_url_rule('/', view_func=self.receive, methods=['POST'])

    def receive(self):
        try:
            encode = self.verify_headers(request.headers)
        except ValueError:
            encode = 'json'
            oc2_body = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed HTTP Headers')
            response = self.consumer.create_response_msg(oc2_body, encode)
        else:
            response = self.consumer.process_command(request.get_data(), encode)

        if response is not None:
            http_response = make_response(response)
            http_response.content_type = f'application/openc2-rsp+{encode};version=1.0'
            return http_response
        else:
            return '', 204

    def start(self):
        serve(self.app, host=self.config.host, port=self.config.port)

    def create_app(self):
        return self.app

    @staticmethod
    def verify_headers(headers):
        """
        Verifies that the HTTP headers for the received OpenC2 Command are valid, and parses the message serialization
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
