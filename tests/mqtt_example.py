import cbor2

from yuuki import (
    Mqtt,
    MqttConfig,
    MQTTAuthorization,
    MQTTAuthentication,
    BrokerConfig,
    Publication,
    Subscription,
    Serialization
)


serializations = [
    Serialization(name='cbor', deserialize=cbor2.loads, serialize=cbor2.dumps)
]

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

consumer = Mqtt(rate_limit=60, versions=['1.0'], mqtt_config=mqtt_config, serializations=serializations)
consumer.start()
