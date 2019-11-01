import re
from collections import namedtuple
from ..common.util  import OC2Cmd, OC2Exception

def convert_raw_cmd(cmd : dict) -> OC2Cmd:
    """Validate then convert a received command; raise ValueError as needed.
    """

    if not isinstance(cmd, dict):
        raise OC2Exception('Received cmd is not a dict')
    
    FieldSchema = namedtuple('FieldSchema', 'name type required validators')

    action     = FieldSchema('action',     str,  True,  ( lambda x: _is_word(x)                 ,))
    target     = FieldSchema('target',     dict, True,  ( lambda x: len(x) == 1                 , 
                                                          lambda x: _is_word(list(x.keys())[0])  ))
    args       = FieldSchema('args',       dict, False, ( lambda x: len(x) >= 1                 ,
                                                          lambda x: _good_args(x)                ))
    actuator   = FieldSchema('actuator',   dict, False, ( lambda x: len(x) >= 1                 ,))
    command_id = FieldSchema('command_id', str,  False, ( lambda x: _is_word(x)                 ,))

    allowed = [action, target, args, actuator, command_id]

    if not all(key in [schema.name for schema in allowed] for key in cmd.keys()):
        raise OC2Exception('Command has invalid fields')

    if not all(key in cmd.keys() for key in [schema.name for schema in allowed if schema.required]):
        raise OC2Exception('Command is missing required fields')

    for schema in allowed:
        value = cmd.get(schema.name)
        if value is not None:
            if not isinstance(value, schema.type):
                raise OC2Exception(f'Command {schema.name} field must be of type {schema.type}')
            for validator in schema.validators:
                if not validator(value):
                    raise OC2Exception(f'Command {schema.name} field failed a validator')
    
    oc2cmd = OC2Cmd(cmd.get('action'),
                    cmd.get('target'),
                    cmd.get('args'),
                    cmd.get('actuator'),
                    cmd.get('command_id')) 

    nsids = _get_any_nsids( oc2cmd)
    if len(nsids) > 1:
        raise OC2Exception(f'Command cannot contain more than one NSID, but found {nsids}')
    
    return oc2cmd

def _is_word(a_str : str) -> bool:
    """
    """
    return bool(re.match(r'\S', a_str))

def _good_args(value : dict) -> bool:
    """
    Non-restrictive; checks for default args, but allows more.
    """

    if not isinstance(value, dict):
        return False
    if not len(value):
        return False
    if value.get('response_requested', 'none') not in ['none',
                                                       'ack',
                                                       'status',
                                                       'complete']:
        return False
    
    cant_have_all = ['start_time',
                     'stop_time',
                     'duration']
    if all(key in value.keys() for key in cant_have_all):
        return False

    for key in cant_have_all:

        check_me = value.get(key, 1)

        if not isinstance(check_me, int):
            return False
    # Any other keys in this dictionary need to be NSID's, with
    # their value being a dictionary.
    basic = cant_have_all + ['response_requested']
    if not all(isinstance(value[nsid_key], dict) for nsid_key in value.keys() if nsid_key not in basic ):
        return False
    
    return True

def _get_any_nsids(cmd : OC2Cmd) -> list:
    """
    """    
    target_field, = cmd.target.keys()

    target_field_nsid = None
    # Handle: 'target' : {'x-acme:extended_target_defined_by_acme' : ...}
    if ':' in target_field:
        target_field_nsid, target_field = target_field.split(':')

    actuator_field_nsid = None
    # Handle: 'actuator' : {'x-amce' : ....}
    if cmd.actuator:
        actuator_field_nsid, = cmd.actuator.keys()
    
    args_field_nsids = []
    # Handle: 'args' : {'slpf' : ..., 'x-acme' : ..., 'response_required' : 'none'}
    if cmd.args:
        for key in cmd.args.keys():
            if key.startswith('x-'):
                args_field_nsids.append(key)
            elif key == 'slpf':
                args_field_nsids.append(key)

    all_nsids = list(set([target_field_nsid, actuator_field_nsid, *args_field_nsids]))

    if None in all_nsids:
        all_nsids.remove(None)
    
    return all_nsids