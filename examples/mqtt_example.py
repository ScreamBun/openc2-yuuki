"""
Example Implementation of an OpenC2 Consumer with MQTT and JSON.

First a Command Handler is defined, then we instantiate
a Consumer with it and our chosen Transport(MQTT) and Serialization(Json).
"""
from yuuki.transport import (
    Mqtt,
    MqttConfig,
    Authorization,
    Authentication,
    BrokerConfig,
    Publish,
    Subscription
)
from command_handler import CommandHandler

# The default options are shown here just for visibility.
# You could just write mqtt_config = MqttConfig() for the same result.

mqtt_config = MqttConfig(
    broker=BrokerConfig(
        socket='test.mosquitto.org:1883',
        client_id='',
        keep_alive=300,
        authorization=Authorization(
            enable=True,
            user_name='plug',
            pw='fest'),
        authentication=Authentication(
            enable=False,
            certfile=None,
            keyfile=None,
            ca_certs=None)),
    subscriptions=[
        Subscription(
            topic_filter='oc2/cmd',
            qos=1)],
    publishes=[
        Publish(
            topic_name='oc2/rsp',
            qos=1
        )]
)

consumer = Mqtt(CommandHandler(), mqtt_config)
consumer.start()
