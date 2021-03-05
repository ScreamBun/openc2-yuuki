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
from quart import (
    Quart,
    request,
    make_response
)

from .base import Transport

@dataclass
class HttpConfig():
    '''Simple Http Configuration to pass to Http Transport init.'''

    consumer_socket : str = '127.0.0.1:9001'
    use_tls : bool = False
    certfile: Optional[str] = None
    keyfile:  Optional[str] = None
    ca_certs: Optional[str] = None


class Http(Transport):
    '''Implements Transport base class for HTTP'''

    def __init__(self, http_config : HttpConfig):
        super().__init__(http_config)
        self.app = Quart(__name__)
        self.setup(self.app)
    
    def process_config(self):
        self.host, port = self.config.consumer_socket.split(':')
        self.port = int(port)

        if self.config.use_tls:
            if self.config.certfile is None and self.config.keyfile is None:
                raise ValueError('TLS requires a keyfile and certfile.')
    
    def setup(self, app):
        @app.route('/', methods=['POST'])
        async def receive():
            raw_data = await request.get_data()
            oc2_rsp = await self.get_response(raw_data)
            http_response = await make_response(oc2_rsp)
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
        

