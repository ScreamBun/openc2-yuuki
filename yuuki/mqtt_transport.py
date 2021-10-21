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

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from .mqtt_config import MqttConfig
from .consumer import Consumer
from .openc2_types import StatusCode, OpenC2Headers, OpenC2RspFields


class Mqtt(Consumer):
    """Implements Transport base class for MQTT"""

    def __init__(self, cmd_handler, mqtt_config: MqttConfig):
        super().__init__(cmd_handler, mqtt_config)
        self._client = mqtt.Client(client_id=self.config.broker.client_id, protocol=mqtt.MQTTv5)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        if self.config.broker.authorization.enable:
            self._client.username_pw_set(username=self.config.broker.authorization.username,
                                         password=self.config.broker.authorization.password)
        if self.config.broker.authentication.enable:
            logging.info('Will use TLS')
            self._client.tls_set(ca_certs=self.config.broker.authentication.ca_certs,
                                 certfile=self.config.broker.authentication.certfile,
                                 keyfile=self.config.broker.authentication.keyfile)

    def _on_connect(self, client, userdata, flags, reasonCode, properties):
        logging.debug('OnConnect')
        for subscription in self.config.subscriptions:
            logging.info(f'Subscribing --> {subscription.topic} {subscription.qos} ...')
            self._client.subscribe(subscription.topic, subscription.qos)

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

        for publication in self.config.publications:
            message_info = self._client.publish(publication.topic, payload=response,
                                                qos=publication.qos, properties=openc2_properties)
            logging.debug(f'Message Info: {message_info}')
            logging.info(f'Publishing --> qos: {publication.qos} \n{response}')

    def start(self):
        try:
            logging.info(f'Connecting --> {self.config.broker.host}:{self.config.broker.port}')
            self._client.connect(host=self.config.broker.host, port=self.config.broker.port,
                                 keepalive=self.config.broker.keep_alive,
                                 clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY, properties=None)
            self._client.loop_forever()
        except ConnectionRefusedError:
            logging.error(f'BrokerConfig at {self.config.broker.host}:{self.config.broker.port} refused connection')
            raise
