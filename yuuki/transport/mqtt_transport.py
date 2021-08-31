"""
MQTT Transport

Contains the transport class to instantiate, and its config to customize.

The transport receives messages, then sends them on to a handler,
and awaits a response to send back.

Use as an argument to a Consumer constructor, eg:

mqtt_config = MqttConfig(broker=...)
mqtt_transport = Mqtt(mqtt_config)
my_openc2_consumer = Consumer(transport=mqtt_transport, ...)
my_openc2_consumer.start()

"""

import asyncio
import socket
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from .consumer import Consumer

from ..openc2.oc2_types import StatusCode, OC2Headers, OC2RspFields

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes


# ----- Configuration -----

@dataclass
class Authorization:
    enable: bool = False
    user_name: Optional[str] = None
    pw: Optional[str] = None


@dataclass
class Authentication:
    enable: bool = False
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    ca_certs: Optional[str] = None


@dataclass
class BrokerConfig:
    socket: str = '127.0.0.1:1833'
    client_id: str = ''
    keep_alive: int = 300
    authorization: Authorization = field(default_factory=Authorization)
    authentication: Authentication = field(default_factory=Authentication)


@dataclass
class Subscription:
    """Topic Filter and QoS for one subscription.

    Create one of these for each command source.
    """
    topic_filter: str = 'yuuki_user/oc2/cmd'
    qos: int = 1


@dataclass
class Publish:
    """Topic Name and QoS for one publish destination.

    Create one of these for each response destination.
    """
    topic_name: str = 'yuuki_user/oc2/rsp'
    qos: int = 1


@dataclass
class MqttConfig:
    """Configuration object to be passed to Mqtt Transport init.

    Accept the defaults or customize as necessary.

    broker: socket, client_id, authorization, authentication
    subscriptions: list of topic_name/qos objects for commands
    publishes: list of topic_filter/qos objects for responses
    """
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    subscriptions: List[Subscription] = field(default_factory=lambda: [Subscription()])
    publishes: List[Publish] = field(default_factory=lambda: [Publish()])


# ----- Transport -----

class Mqtt(Consumer):
    """Implements Transport base class for MQTT"""

    def __init__(self, cmd_handler, mqtt_config: MqttConfig):
        super().__init__(cmd_handler, mqtt_config)
        self.in_msg_queue = asyncio.Queue()
        self.host, port = self.transport_config.broker.socket.split(':')
        self.port = int(port)

    def start(self):
        mqtt_client = _MqttClient(cmd_subs=self.transport_config.subscriptions,
                                  rsp_pubs=self.transport_config.publishes,
                                  host=self.host,
                                  port=self.port,
                                  keep_alive=self.transport_config.broker.keep_alive,
                                  use_credentials=self.transport_config.broker.authorization.enable,
                                  user_name=self.transport_config.broker.authorization.user_name,
                                  password=self.transport_config.broker.authorization.pw,
                                  client_id=self.transport_config.broker.client_id,
                                  use_tls=self.transport_config.broker.authentication.enable,
                                  ca_certs=self.transport_config.broker.authentication.ca_certs,
                                  certfile=self.transport_config.broker.authentication.certfile,
                                  keyfile=self.transport_config.broker.authentication.keyfile)

        mqtt_client.msg_handler = self.on_oc2_msg
        mqtt_client.connect()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(mqtt_client.main())

    async def on_oc2_msg(self, msg, response_queue):
        """Called whenever our real mqtt client gets a message"""

        encode = self.verify_properties(msg.properties)
        if encode:
            oc2_msg = self.get_response(msg.payload, encode)
        else:
            oc2_body = OC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed MQTT Properties')
            oc2_msg = self.make_response_msg(oc2_body, OC2Headers(), 'json')
        try:
            if oc2_msg is not None:
                response_queue.put_nowait((oc2_msg, encode))
        except Exception as e:
            logging.error(f'Message Handling Failed {e}')

    @staticmethod
    def verify_properties(properties):
        logging.debug(f'Message Properties: {properties}')
        payload_fmt = getattr(properties, 'PayloadFormatIndicator', None)
        content_type = getattr(properties, 'ContentType', None)
        user_property = getattr(properties, 'UserProperty', None)

        if user_property:
            user_props = dict(user_property)
            if "encoding" in user_props.keys():
                encode = user_props["encoding"]
                if (payload_fmt == 1 and content_type == "application/openc2" and
                        user_property == [("msgType", "req"), ("encoding", encode)]):
                    return encode
        return None


class _MqttClient:
    """Wrapper around the paho mqtt client"""

    def __init__(self,
                 cmd_subs,
                 rsp_pubs,
                 host,
                 port,
                 keep_alive,
                 use_credentials,
                 user_name,
                 password,
                 client_id,
                 use_tls,
                 ca_certs,
                 certfile,
                 keyfile):
        self.cmd_subs = cmd_subs
        self.rsp_pubs = rsp_pubs
        self.host = host
        self.port = port
        self.keep_alive = keep_alive
        self.use_credentials = use_credentials
        self.user_name = user_name
        self.password = password
        self.client_id = client_id
        self.use_tls = use_tls
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile

        self._client = None
        self.msg_handler = None
        self.loop = asyncio.get_event_loop()
        self.misc_loop_task = None
        self.in_msg_queue = asyncio.Queue()
        self.out_msg_queue = asyncio.Queue()

        self.setup_client()
        self.disconnected = self.loop.create_future()

    def setup_client(self):
        self._client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv5)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_socket_open = self.on_socket_open
        self._client.on_socket_close = self.on_socket_close
        self._client.on_socket_register_write = self.on_socket_register_write
        self._client.on_socket_unregister_write = self.on_socket_unregister_write

        if self.use_credentials:
            self._client.username_pw_set(self.user_name, password=self.password)

    def _on_connect(self, client, userdata, flags, reasonCode, properties):
        logging.debug('OnConnect')
        for sub_info in self.cmd_subs:
            self.subscribe(sub_info.topic_filter, sub_info.qos)

    def _on_message(self, client, userdata, msg):
        logging.debug(f'OnMessage: {msg.payload}')
        self.in_msg_queue.put_nowait(msg)

    def _on_disconnect(self, client, userdata, reasonCode, properties=None):
        logging.debug('OnDisconnect')
        self.disconnected.set_result('disconnected')

    def on_socket_open(self, client, userdata, sock):
        def cb():
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc_loop_task = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        self.loop.remove_reader(sock)
        self.misc_loop_task.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        def cb():
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        while True:
            if self._client.loop_misc() != mqtt.MQTT_ERR_SUCCESS:
                break
            while self.out_msg_queue.qsize() > 0:
                response, encode = self.out_msg_queue.get_nowait()
                self.out_msg_queue.task_done()
                for rsp_pub_info in self.rsp_pubs:
                    self.publish(rsp_pub_info.topic_name, response, rsp_pub_info.qos, encode)
            if self.in_msg_queue.qsize() > 0:
                msg = self.in_msg_queue.get_nowait()
                self.in_msg_queue.task_done()
                try:
                    await self.msg_handler(msg, self.out_msg_queue)
                except Exception as e:
                    logging.error(e)
                    raise
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    def connect(self):
        try:
            if self.use_tls:
                logging.info('Will use TLS')
                self._client.tls_set(ca_certs=self.ca_certs, certfile=self.certfile, keyfile=self.keyfile)
            logging.info(f'Connecting --> {self.host}:{self.port} --> keep_alive:{self.keep_alive} ...')
            self._client.connect(self.host, self.port, keepalive=self.keep_alive,
                                 clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY, properties=None)
        except ConnectionRefusedError:
            logging.error(f'BrokerConfig at {self.host}:{self.port} refused connection')
            raise
        self._client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    def subscribe(self, topic_filter, qos):
        logging.info(f'Subscribing --> {topic_filter} {qos} ...')
        self._client.subscribe(topic_filter, qos)

    def publish(self, topic, payload, qos, encode):
        try:
            oc2_properties = Properties(PacketTypes.PUBLISH)
            oc2_properties.PayloadFormatIndicator = 1
            oc2_properties.ContentType = "application/openc2"
            oc2_properties.UserProperty = [("msgType", "rsp"), ("encoding", encode)]

            msg_info = self._client.publish(topic, payload=payload, qos=qos, properties=oc2_properties)
            logging.debug(f'Message Info: {msg_info}')
            logging.info(f'Publishing --> qos: {qos} \n{payload}')
        except Exception as e:
            logging.error('Publish failed', e)

    def disconnect(self):
        self._client.disconnect()

    async def main(self):
        try:
            await self.disconnected
        except asyncio.CancelledError:
            pass
