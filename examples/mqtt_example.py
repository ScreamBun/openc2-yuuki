"""
Example Implementation of an OpenC2 MQTT Consumer
"""
import argparse

from yuuki.transports import (
    MqttTransport,
    MqttConfig,
    MQTTAuthorization,
    MQTTAuthentication,
    BrokerConfig,
    Publication,
    Subscription
)

from consumer_example import consumer

parser = argparse.ArgumentParser(description="MQTT Consumer")
parser.add_argument("--host", help="MQTT Broker host")
parser.add_argument("--port", type=int, help="MQTT Broker port")
args = parser.parse_args()

host = args.host if args.host is not None else "127.0.0.1"
port = args.port if args.port is not None else 1883

mqtt_config = MqttConfig(
    broker=BrokerConfig(
        host=host,
        port=port,
        client_id='',
        keep_alive=300,
        authorization=MQTTAuthorization(
            enable=True,
            username=None,
            password=None),
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

mqtt_consumer = MqttTransport(consumer=consumer, config=mqtt_config)
mqtt_consumer.start()
