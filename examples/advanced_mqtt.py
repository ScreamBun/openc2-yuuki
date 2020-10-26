"""
Example Implementation of an OpenC2 Consumer with MQTT and JSON.

First a Command Handler is defined, then we instantiate
a Consumer with it and our chosen Transport(MQTT) and Serialization(Json).
"""

import logging
import random

from yuuki.openc2.message_dispatch import (
    OpenC2CmdDispatchBase,
    oc2_pair, 
    oc2_query_features,
    oc2_no_matching_pair,
    oc2_no_matching_actuator
)

from yuuki.openc2.oc2_types import (
    OC2Rsp,
    OC2Cmd,
    StatusCode
)

from yuuki.consumer import (
    Consumer
)

from yuuki.openc2.validate import validate_and_convert
from yuuki.serialize import Json
from yuuki.transport import (
    Mqtt,
    MqttConfig,
    Authorization,
    Authentication,
    BrokerConfig, 
    Publish, 
    Subscription
)

logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.INFO)

class CmdHandler(OpenC2CmdDispatchBase):
    '''
    The command handler for an OpenC2 Consumer that implements:
    * slpf: Stub implementation of State-Less Packet Filter
    * x-acme: Stub implementation of Roadrunner hunting

    Add methods to handle OpenC2 Commands, and tag them with 
    the oc2_pair decorator. The method names do not matter:

    @oc2_pair(ACTUATOR_NSID, ACTION, TARGET)
    def some_method(self, OC2Command):
        return OC2Rsp
    '''
    def __init__(self, validator=None):
        super().__init__(validator)
    
    @property
    def versions(self):
        '''
        List of OpenC2 language versions supported by this Actuator.
        (3.3.2.2 Response Results)
        '''
        return ['1.0']

    @property
    def profiles(self):
        '''
        List of profiles supported by this Actuator.
        (3.3.2.2 Response Results)
        '''
        return ['slpf', 'x-acme']
    
    @property
    def rate_limit(self):
        '''
        Maximum number of requests per minute supported by design or policy.
        (3.3.2.2 Response Results)
        '''
        return 60

    @oc2_query_features
    def func1(self, oc2_cmd : OC2Cmd) -> OC2Rsp:
        '''
        Handle all calls to the OpenC2 command 'query features'.
        The parent class comes with a built-in method for this.
        '''
        oc2_rsp = super().query_features(oc2_cmd)

        return oc2_rsp

    @oc2_pair('slpf', 'deny', 'ipv4_connection')
    def func2(self, oc2_cmd : OC2Cmd) -> OC2Rsp:
        '''
        Stub for the SLPF OpenC2 Command 'deny ipv4_connection'.
        '''
        allowed_keys = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'protocol']
        found_keys = []
        found_other = []
        if isinstance(oc2_cmd.target['ipv4_connection'], dict):
            for key in oc2_cmd.target['ipv4_connection'].keys():
                if key in allowed_keys:
                    found_keys.append(key)
                else:
                    found_other.append(key)

        if len(found_keys) < 1 or len(found_other) > 0:
            oc2_rsp = OC2Rsp(
                status=StatusCode.BAD_REQUEST,
                status_text='Any of {} required for ipv4_connection'.format(str(allowed_keys)))
            return oc2_rsp

        # Execute a firewall function here to deny...
        
        # For now, return what we would do.
        status_text = 'Denied ipv4_connection: {}'.format(oc2_cmd.target['ipv4_connection'])

        oc2_rsp = OC2Rsp(
            status=StatusCode.OK,
            status_text=status_text)

        return oc2_rsp
    
    @oc2_pair('x-acme', 'detonate', 'x-acme:roadrunner' )
    def func3(self, oc2_cmd : OC2Cmd) -> OC2Rsp:
        '''
        Custom actuator profile implementation for Road Runner hunting.
        '''
        coyote_possibilites = [True, False]
        coyote_success = random.choice(coyote_possibilites)

        if coyote_success:
            raise SystemError('Example of how exceptions here are caught')
        else:
            return OC2Rsp(
                status=StatusCode.INTERNAL_ERROR,
                status_text='Coyote can never win')

    @oc2_no_matching_pair
    def func4(self, oc2_cmd : OC2Cmd) -> OC2Rsp:
        '''
        We've searched all our action-target pairs from all our
        actuators, and that pair doesn't exist.
        '''
        oc2_rsp = OC2Rsp(
            status=StatusCode.NOT_FOUND,
            status_text='No action-target pair for {} {}'.format(oc2_cmd.action, oc2_cmd.target_name))

        return oc2_rsp

    @oc2_no_matching_actuator
    def func5(self, oc2_cmd : OC2Cmd) -> OC2Rsp:
        '''
        We have a matching action-target pair in our actuator(s),
        but we don't have the requested actuator (nsid).
        '''
        actuator_name, = oc2_cmd.actuator.keys()
        oc2_rsp = OC2Rsp(
            status=StatusCode.NOT_FOUND,
            status_text='No actuator {}'.format(actuator_name))

        return oc2_rsp

if __name__ == '__main__':

    # The default options are shown here just for visibility.
    # You could just write
    # mqtt_config = MqttConfig() for the same result.
    
    mqtt_config = MqttConfig(
                    broker=BrokerConfig(
                        socket='34.86.117.113:1883',
                        client_id='',
                        keep_alive=60,
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
                            topic_filter='patrickc/oc2/cmd',
                            qos=1)],
                    publishes=[
                        Publish(
                            topic_name='patrickc/oc2/rsp',
                            qos=1
                        )]
                    )
    
    consumer = Consumer(
        cmd_handler=CmdHandler(validator=validate_and_convert),
        transport=Mqtt(mqtt_config),
        serialization=Json )

    try:
        consumer.start()
    except KeyboardInterrupt:
        pass