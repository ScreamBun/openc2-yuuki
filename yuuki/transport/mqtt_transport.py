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

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from .consumer import Consumer
from ..openc2.openc2_types import StatusCode, OpenC2Headers, OpenC2RspFields


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
        self.host, port = self.transport_config.broker.socket.split(':')
        self.port = int(port)
        self.cmd_subs = self.transport_config.subscriptions
        self.rsp_pubs = self.transport_config.publishes
        self.host = self.host
        self.port = self.port
        self.keep_alive = self.transport_config.broker.keep_alive
        self.use_credentials = self.transport_config.broker.authorization.enable
        self.user_name = self.transport_config.broker.authorization.user_name
        self.password = self.transport_config.broker.authorization.pw
        self.client_id = self.transport_config.broker.client_id
        self.use_tls = self.transport_config.broker.authentication.enable
        self.ca_certs = self.transport_config.broker.authentication.ca_certs
        self.certfile = self.transport_config.broker.authentication.certfile
        self.keyfile = self.transport_config.broker.authentication.keyfile

        self._client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv5)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        if self.use_credentials:
            self._client.username_pw_set(self.user_name, password=self.password)

    def _on_connect(self, client, userdata, flags, reasonCode, properties):
        logging.debug('OnConnect')
        for sub_info in self.cmd_subs:
            logging.info(f'Subscribing --> {sub_info.topic_filter} {sub_info.qos} ...')
            self._client.subscribe(sub_info.topic_filter, sub_info.qos)

    def _on_message(self, client, userdata, msg):
        logging.debug(f'OnMessage: {msg.payload}')
        try:
            encode = self.verify_properties(msg.properties)
        except ValueError:
            encode = 'json'
            oc2_body = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed MQTT Properties')
            response = self.make_response_msg(oc2_body, OpenC2Headers(), encode)
        else:
            response = self.get_response(msg.payload, encode)

        if response is not None:
            try:
                self.publish_response_messages(response, encode)
            except Exception as e:
                logging.error('Publish failed', e)

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
        raise ValueError('Invalid OpenC2 MQTT Properties')

    def publish_response_messages(self, response, encode):
        openc2_properties = Properties(PacketTypes.PUBLISH)
        openc2_properties.PayloadFormatIndicator = 1
        openc2_properties.ContentType = "application/openc2"
        openc2_properties.UserProperty = [("msgType", "rsp"), ("encoding", encode)]

        for rsp_pub_info in self.rsp_pubs:
            message_info = self._client.publish(rsp_pub_info.topic_name, payload=response,
                                                qos=rsp_pub_info.qos, properties=openc2_properties)
            logging.debug(f'Message Info: {message_info}')
            logging.info(f'Publishing --> qos: {rsp_pub_info.qos} \n{response}')

    def start(self):
        try:
            if self.use_tls:
                logging.info('Will use TLS')
                self._client.tls_set(ca_certs=self.ca_certs, certfile=self.certfile, keyfile=self.keyfile)
            logging.info(f'Connecting --> {self.host}:{self.port} --> keep_alive:{self.keep_alive} ...')
            self._client.connect(self.host, self.port, keepalive=self.keep_alive,
                                 clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY, properties=None)
            self._client.loop_forever()
        except ConnectionRefusedError:
            logging.error(f'BrokerConfig at {self.host}:{self.port} refused connection')
            raise
