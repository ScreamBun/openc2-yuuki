"""
Example Implementation of an OpenC2 Consumer with HTTP and JSON.

First a Command Handler is defined, then we instantiate
a Consumer with it and our chosen Transport(HTTP) and Serialization(Json).

To keep the file short and sweet, we use wildcard * imports and no comments.
See the mqtt_example.py for details.
"""

import logging
from ipaddress import ip_network
from yuuki import *

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class CmdHandler(OpenC2CmdDispatchBase):
    def __init__(self, validator=None):
        super().__init__(validator)

    @property
    def versions(self):
        return ['1.0']

    @property
    def profiles(self):
        return ['slpf', 'x-acme']

    @property
    def rate_limit(self):
        return 60

    @oc2_query_features
    def func1(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        return super().query_features(oc2_cmd)

    @oc2_pair('slpf', 'deny', 'ipv4_connection')
    def func2(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
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
            return OC2Rsp(status=StatusCode.BAD_REQUEST)

        # Execute a real function here to deny...

        return OC2Rsp(status=StatusCode.OK)

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
        raise SystemError('Impossible! Coyote never wins!')

    @oc2_no_matching_pair
    def func5(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        return OC2Rsp(status=StatusCode.NOT_FOUND,
                      status_text=f'No action-target pair for {oc2_cmd.action} {oc2_cmd.target_name}')

    @oc2_no_matching_actuator
    def func6(self, oc2_cmd: OC2Cmd) -> OC2Rsp:
        actuator_name, = oc2_cmd.actuator.keys()
        return OC2Rsp(status=StatusCode.NOT_FOUND, status_text=f'No actuator {actuator_name}')


if __name__ == '__main__':
    http_config = HttpConfig()

    consumer = Consumer(cmd_handler=CmdHandler(validator=validate_and_convert), transport=Http(http_config))
    consumer.start()
