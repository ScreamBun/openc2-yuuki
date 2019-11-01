from collections import namedtuple

OC2Cmd = namedtuple('OC2Cmd', 'action target args actuator command_id')
Pair   = namedtuple('Pair', 'action target')


class OC2ExceptionBase(Exception):
    pass

class OC2Exception(OC2ExceptionBase):
    pass