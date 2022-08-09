"""Profile for Stateless Packet Filtering Version 1.0
https://docs.oasis-open.org/openc2/oc2slpf/v1.0/oc2slpf-v1.0.html
Conformant to Conformance Clauses 12, 14, 16
"""

from ipaddress import ip_network

from yuuki import Actuator, OpenC2CmdFields, OpenC2RspFields, StatusCode

slpf = Actuator(nsid='slpf')


@slpf.pair('deny', 'ipv4_connection', implemented=False)
def deny_ipv4_connection(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@slpf.pair('allow', 'ipv4_connection', implemented=False)
def allow_ipv4_connection(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@slpf.pair('deny', 'ipv6_connection')
def deny_ipv6_connection(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    allowed_keys = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'protocol']
    found_keys = []
    found_other = []
    if isinstance(oc2_cmd.target['ipv6_connection'], dict):
        for key in oc2_cmd.target['ipv6_connection'].keys():
            if key in allowed_keys:
                found_keys.append(key)
            else:
                found_other.append(key)

    if len(found_keys) < 1 or len(found_other) > 0:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                               status_text=f'Any of {str(allowed_keys)} required for ipv6_connection')

    unimplemented_args = ['persistent', 'direction', 'drop_process', 'start_time', 'stop_time', 'duration']
    if oc2_cmd.args is not None and any(arg in oc2_cmd.args.dict(exclude_unset=True) for arg in unimplemented_args):
        return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED,
                               status_text=f'Arguments: {unimplemented_args} are unsupported')
    # Execute a firewall function here to deny...

    # For now, return what we would do.
    status_text = f'Denied ipv6_connection: {oc2_cmd.target["ipv6_connection"]}'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@slpf.pair('allow', 'ipv6_connection')
def allow_ipv6_connection(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    allowed_keys = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'protocol']
    found_keys = []
    found_other = []
    if isinstance(oc2_cmd.target['ipv6_connection'], dict):
        for key in oc2_cmd.target['ipv6_connection'].keys():
            if key in allowed_keys:
                found_keys.append(key)
            else:
                found_other.append(key)

    if len(found_keys) < 1 or len(found_other) > 0:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                               status_text=f'Any of {str(allowed_keys)} required for ipv6_connection')

    unimplemented_args = ['persistent', 'direction', 'start_time', 'stop_time', 'duration']
    if oc2_cmd.args is not None and any(arg in oc2_cmd.args.dict(exclude_unset=True) for arg in unimplemented_args):
        return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED,
                               status_text=f'Arguments: {unimplemented_args} are unsupported')
    # Execute a firewall function here to allow...

    # For now, return what we would do.
    status_text = f'Allowed ipv6_connection: {oc2_cmd.target["ipv6_connection"]}'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@slpf.pair('deny', 'ipv4_net', implemented=False)
def deny_ipv4_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@slpf.pair('allow', 'ipv4_net', implemented=False)
def allow_ipv4_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@slpf.pair('deny', 'ipv6_net')
def deny_ipv6_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    if isinstance(oc2_cmd.target['ipv6_net'], str):
        try:
            ip_network(oc2_cmd.target['ipv6_net'])
        except ValueError:
            return OpenC2RspFields(status=StatusCode.BAD_REQUEST)
        else:
            unimplemented_args = ['persistent', 'direction', 'drop_process', 'start_time', 'stop_time', 'duration']
            if oc2_cmd.args and any(arg in oc2_cmd.args.dict(exclude_unset=True) for arg in unimplemented_args):
                return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED,
                                       status_text=f'Arguments: {unimplemented_args} are unsupported')
            # Execute a real function here to deny...
            pass
        return OpenC2RspFields(status=StatusCode.OK)
    else:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST)


@slpf.pair('allow', 'ipv6_net')
def allow_ipv6_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    if isinstance(oc2_cmd.target['ipv6_net'], str):
        try:
            ip_network(oc2_cmd.target['ipv6_net'])
        except ValueError:
            return OpenC2RspFields(status=StatusCode.BAD_REQUEST)
        else:
            unimplemented_args = ['persistent', 'direction', 'start_time', 'stop_time', 'duration']
            if oc2_cmd.args and any(arg in oc2_cmd.args.dict(exclude_unset=True) for arg in unimplemented_args):
                return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED,
                                       status_text=f'Arguments: {unimplemented_args} are unsupported')
            # Execute a real function here to allow...
            pass
        return OpenC2RspFields(status=StatusCode.OK)
    else:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST)


@slpf.pair('update', 'file', implemented=False)
def update_file(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@slpf.pair('delete', 'slpf:rule_number', implemented=False)
def delete_rule_number(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
