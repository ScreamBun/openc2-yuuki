from typing import Optional, List

from pydantic import BaseModel, BaseSettings, validator


class MQTTAuthorization(BaseSettings):
    enable: bool = False
    username: Optional[str] = None
    password: Optional[str] = None


class MQTTAuthentication(BaseSettings):
    enable: bool = False
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    ca_certs: Optional[str] = None


class BrokerConfig(BaseSettings):
    host: str = '127.0.0.1'
    port: int = 1883
    client_id: str = ''
    keep_alive: int = 300
    authorization: MQTTAuthorization = MQTTAuthorization()
    authentication: MQTTAuthentication = MQTTAuthentication()


class Subscription(BaseSettings):
    """Topic Filter and QoS for one subscription.

    Create one of these for each command source.
    """
    topic: str = 'oc2/cmd'
    qos: int = 1

    @validator('qos')
    def validate_target_length(cls, qos):
        if qos not in {1, 2}:
            raise ValueError('QoS level must be 1 or 2')
        return qos


class Publication(BaseSettings):
    """Topic Name and QoS for one publish destination.

    Create one of these for each response destination.
    """
    topic: str = 'oc2/rsp'
    qos: int = 1

    @validator('qos')
    def validate_target_length(cls, qos):
        if qos not in {1, 2}:
            raise ValueError('QoS level must be 1 or 2')
        return qos


class MqttConfig(BaseSettings):
    """Configuration object to be passed to Mqtt Transport init.

    Accept the defaults or customize as necessary.

    broker: socket, client_id, authorization, authentication
    subscriptions: list of topic/qos objects for commands
    publications: list of topic/qos objects for responses
    """
    broker: BrokerConfig = BrokerConfig()
    subscriptions: List[Subscription] = [Subscription()]
    publications: List[Publication] = [Publication()]
