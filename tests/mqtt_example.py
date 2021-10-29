"""
Example Implementation of an OpenC2 Consumer with MQTT and JSON.

First a Command Handler is defined, then we instantiate
a Consumer with it and our chosen Transport(MQTT) and Serialization(Json).
"""

from yuuki import (
    Mqtt,
    MqttConfig,
    MQTTAuthorization,
    MQTTAuthentication,
    BrokerConfig,
    Publication,
    Subscription
)
from command_handler import testcmdhandler


mqtt_config = MqttConfig(
    broker=BrokerConfig(
        host='test.mosquitto.org',
        port=1883,
        client_id='',
        keep_alive=300,
        authorization=MQTTAuthorization(
            enable=True,
            username='plug',
            password='fest'),
        authentication=MQTTAuthentication(
            enable=False,
            certfile=None,
            keyfile=None,
            ca_certs=None)),
    subscriptions=[
        Subscription(
            topic='oc2/cmd',
            qos=1)],
    publications=[
        Publication(
            topic='oc2/rsp',
            qos=1
        )]
)

consumer = Mqtt(testcmdhandler, mqtt_config)
consumer.start()
