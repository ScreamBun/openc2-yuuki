import logging
import random
from ipaddress import ip_network

from yuuki import OpenC2Dispatch, OpenC2CmdFields, OpenC2RspFields, StatusCode

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

testcmdhandler = OpenC2Dispatch(60, ['1.0'])


@testcmdhandler.openc2_pair('deny', 'ipv4_connection', 'slpf')
def deny_ipv4_connection(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
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
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                               status_text=f'Any of {str(allowed_keys)} required for ipv4_connection')

    # Execute a firewall function here to deny...

    # For now, return what we would do.
    status_text = f'Denied ipv4_connection: {oc2_cmd.target["ipv4_connection"]}'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@testcmdhandler.openc2_pair('deny', 'ipv4_net', 'slpf')
def deny_ipv4_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    if isinstance(oc2_cmd.target['ipv4_net'], str):
        try:
            ip_network(oc2_cmd.target['ipv4_net'])
        except ValueError:
            return OpenC2RspFields(status=StatusCode.BAD_REQUEST)
        else:
            # Execute a real function here to deny...
            pass
        return OpenC2RspFields(status=StatusCode.OK)
    else:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST)


@testcmdhandler.openc2_pair('detonate', 'x-acme:roadrunner', 'x-acme')
def roadrunner(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    """
    Custom actuator profile implementation for Road Runner hunting.
    """
    coyote_possibilities = [True, False]
    coyote_success = random.choice(coyote_possibilities)

    if coyote_success:
        raise SystemError('Example of how exceptions here are caught')
    else:
        return OpenC2RspFields(status=StatusCode.INTERNAL_ERROR, status_text='Coyote can never win')
