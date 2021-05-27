"""
Example Implementation of an OpenC2 Consumer with MQTT and JSON.

First a Command Handler is defined, then we instantiate
a Consumer with it and our chosen Transport(MQTT) and Serialization(Json).
"""

import logging
import random
from ipaddress import ip_network

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

from yuuki.transport import (
    Mqtt,
    MqttConfig,
    Authorization,
    Authentication,
    BrokerConfig,
    Publish,
    Subscription
)

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


class CmdHandler(OpenC2CmdDispatchBase):
    """
    The command handler for an OpenC2 Consumer that implements:
    * slpf: Stub implementation of State-Less Packet Filter
    * x-acme: Stub implementation of Roadrunner hunting

    Add methods to handle OpenC2 Commands, and tag them with
    the oc2_pair decorator. The method names do not matter:

    @oc2_pair(ACTUATOR_NSID, ACTION, TARGET)
    def some_method(self, OC2Command):
        return OC2Rsp
    """

    @property
    def versions(self):
        """
        List of OpenC2 language versions supported by this Actuator.
        (3.3.2.2 Response Results)
        """
        return ['1.0']

    @property
    def profiles(self):
        """
        List of profiles supported by this Actuator.
        (3.3.2.2 Response Results)
        """
        return ['slpf', 'x-acme']

    @property
    def rate_limit(self):
        """
        Maximum number of requests per minute supported by design or policy.
        (3.3.2.2 Response Results)
        """
        return 60

    @oc2_query_features
    def func1(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        """
        Handle all calls to the OpenC2 command 'query features'.
        The parent class comes with a built-in method for this.
        """
        oc2_rsp = super().query_features(oc2_cmd)

        return oc2_rsp

    @oc2_pair('slpf', 'deny', 'ipv4_connection')
    def func2(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        """
        Stub for the SLPF OpenC2 Command 'deny ipv4_connection'.
        """
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
            return OC2Rsp(status=StatusCode.BAD_REQUEST,
                          status_text=f'Any of {str(allowed_keys)} required for ipv4_connection')

        # Execute a firewall function here to deny...

        # For now, return what we would do.
        status_text = f'Denied ipv4_connection: {oc2_cmd.target["ipv4_connection"]}'
        return OC2Rsp(status=StatusCode.OK, status_text=status_text)

    @oc2_pair('slpf', 'deny', 'ipv4_net')
    def func3(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        if isinstance(oc2_cmd.target['ipv4_net'], str):
            try:
                ip_network(oc2_cmd.target['ipv4_net'])
            except ValueError:
                return OC2Rsp(status=StatusCode.BAD_REQUEST)
            else:
                # Execute a real function here to deny...
                pass
            return OC2Rsp(status=StatusCode.OK)
        else:
            return OC2Rsp(status=StatusCode.BAD_REQUEST)

    @oc2_pair('x-acme', 'detonate', 'x-acme:roadrunner')
    def func4(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        """
        Custom actuator profile implementation for Road Runner hunting.
        """
        coyote_possibilites = [True, False]
        coyote_success = random.choice(coyote_possibilites)

        if coyote_success:
            raise SystemError('Example of how exceptions here are caught')
        else:
            return OC2Rsp(status=StatusCode.INTERNAL_ERROR, status_text='Coyote can never win')

    @oc2_no_matching_pair
    def func5(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        """
        We've searched all our action-target pairs from all our
        actuators, and that pair doesn't exist.
        """
        return OC2Rsp(status=StatusCode.NOT_FOUND,
                      status_text=f'No action-target pair for {oc2_cmd.action} {oc2_cmd.target_name}')

    @oc2_no_matching_actuator
    def func6(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        """
        We have a matching action-target pair in our actuator(s),
        but we don't have the requested actuator (nsid).
        """
        actuator_name, = oc2_cmd.actuator.keys()
        return OC2Rsp(status=StatusCode.NOT_FOUND, status_text=f'No actuator {actuator_name}')


if __name__ == '__main__':

    # The default options are shown here just for visibility.
    # You could just write
    # mqtt_config = MqttConfig() for the same result.

    mqtt_config = MqttConfig(
        broker=BrokerConfig(
            socket='172.16.0.57:1883',
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
                topic_filter='yuuki/oc2/cmd',
                qos=1)],
        publishes=[
            Publish(
                topic_name='yuuki/oc2/rsp',
                qos=1
            )]
    )

    consumer = Mqtt(CmdHandler(), mqtt_config)

    try:
        consumer.start()
    except KeyboardInterrupt:
        pass
