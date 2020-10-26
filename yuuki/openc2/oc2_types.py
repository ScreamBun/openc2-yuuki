"""Basic OpenC2 Types: Command, Response, etc"""

from dataclasses import dataclass, field, asdict
import pprint
import time
from enum import Enum
from collections import UserDict, namedtuple
from typing import Optional, List, Dict, Mapping, Any, Iterable, Union


#OC2Cmd = namedtuple('OC2Cmd', 'action target target_name args actuator command_id')
Pair = namedtuple('Pair', 'action target')

class StatusCode(Enum):
    PROCESSING = 102
    OK = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503
    
    def text(self):
        mapping = {
            102: 'Processing - an interim OC2Rsp used to inform the Producer that the Consumer has accepted the Command but has not yet completed it.',
            200: 'OK - the Command has succeeded.',
            400: 'Bad Request - the Consumer cannot process the Command due to something that is perceived to be a Producer error (e.g., malformed Command syntax).',
            401: 'Unauthorized - the Command Message lacks valid authentication credentials for the target resource or authorization has been refused for the submitted credentials.',
            403: 'Forbidden - the Consumer understood the Command but refuses to authorize it.',
            404: 'Not Found - the Consumer has not found anything matching the Command.',
            500: 'Internal Error - the Consumer encountered an unexpected condition that prevented it from performing the Command.',
            501: 'Not Implemented - the Consumer does not support the functionality required to perform the Command.',
            503: 'Service Unavailable - the Consumer is currently unable to perform the Command due to a temporary overloading or maintenance of the Consumer.'
        }
        return mapping[self.value]

    def __repr__(self):
        return str(self.value)

# ---Notification---

@dataclass
class OC2Nfy():
    pass

@dataclass
class OC2NfyParent():
    notification : field(default_factory=OC2Nfy)

# ---Response---

@dataclass
class OC2Rsp():
    status : StatusCode = StatusCode.NOT_IMPLEMENTED
    status_text : Optional[str] = None
    results : Optional[Dict[str,str]] = None

    def __post_init__(self):
        if self.status_text is None:
            self.status_text = self.status.text()

    def keys_for_serializing(self):
        retval = ['status']
        for attr_name in ['status_text', 'results']:
            if getattr(self, attr_name) is not None:
                retval.append(attr_name)
        
        return retval

    @classmethod
    def init_from_dict(cls, a_dict):
        retval = cls()
        if isinstance(a_dict['status'], (int,str)):
            retval.status = StatusCode(int(a_dict['status']))
        for attr_name in ['status_text', 'results']:
            if attr_name in a_dict.keys():
                setattr(retval, attr_name, a_dict[attr_name])
        return retval


@dataclass
class OC2RspParent():
    response : OC2Rsp = field(default_factory=OC2Rsp)

    @classmethod
    def init_from_dict(cls, a_dict):
        retval = cls()
        if 'response' in a_dict.keys():
            retval.response = OC2Cmd.init_from_dict(a_dict['response'])
        return retval


# ---Command---

@dataclass
class OC2Cmd():
    action : str = 'deny'
    target : Mapping[str,Any] = field(default_factory=lambda : {'ipv4_connection': {}})
    args   : Optional[Mapping[str,Mapping[Any,Any]]] = None
    actuator : Optional[Mapping[str,Mapping[Any,Any]]] = None
    command_id : Optional[str] = None

    @property
    def target_name(self):
        retval, = self.target.keys()
        return retval
    
    @property
    def actuator_name(self):
        if self.actuator is not None:
            retval, = self.actuator.keys()
            return retval
        return None

    def keys_for_serializing(self):
        retval = ['action', 'target']
        for attr_name in ['args', 'actuator', 'command_id']:
            if getattr(self, attr_name) is not None:
                retval.append(attr_name)
        
        return retval
    
    @classmethod
    def init_from_dict(cls, a_dict):
        retval = cls()
        retval.action = a_dict['action']
        retval.target = a_dict['target']
        
        for attr_name in ['args', 'actuator', 'command_id']:
            if attr_name in a_dict.keys():
                setattr(self, attr_name, a_dict[attr_name])
        return retval


@dataclass
class OC2CmdParent():
    request : OC2Cmd = field(default_factory=OC2Cmd)

    @classmethod
    def init_from_dict(cls, a_dict):
        retval = cls()
        if 'request' in a_dict.keys():
            retval.request = OC2Cmd.init_from_dict(a_dict['request'])
        return retval

# -----------

@dataclass
class Headers():
    request_id : Optional[str] = None
    created : Optional[int] = None
    from_  : Optional[str] = None
    to    : Optional[Iterable[str]] = None

    @classmethod
    def init_from_dict(cls, a_dict):
        retval = cls()
        for attr_name in ['request_id', 'created', 'to']:
            if attr_name in a_dict.keys():
                setattr(retval, attr_name, a_dict[attr_name])
        if 'from' in a_dict.keys():
            setattr(retval, 'from_', a_dict['from'])

        return retval

@dataclass
class Body():
    openc2 : Union[OC2CmdParent, OC2RspParent, OC2NfyParent] = field(default_factory=OC2CmdParent)

    @classmethod
    def init_from_dict(cls, a_dict):
        retval = cls()
        my_root = a_dict['openc2']
        if 'request' in my_root.keys():
            retval.openc2 = OC2CmdParent.init_from_dict(my_root)
        elif 'response' in my_root.keys():
            retval.openc2 = OC2RspParent.init_from_dict(my_root)
        elif 'notification' in my_root.keys():
            retval.openc2 = OC2NfyParent.init_from_dict(my_root)
        return retval

@dataclass
class OC2Msg():
    headers : Headers = field(default_factory=Headers)
    body : Body = field(default_factory=Body)

    @classmethod
    def init_from_dict(cls, a_dict):
        retval = cls()
        if 'headers' in a_dict.keys():
            retval.headers = Headers.init_from_dict(a_dict['headers'])
        if 'body' in a_dict.keys():
            retval.body = Body.init_from_dict(a_dict['body'])
        return retval

    def to_dict(self):
        retval = asdict(self)
        if 'headers' in retval.keys():
            if 'from_' in retval['headers'].keys():
                retval['headers']['from'] = retval['headers'].pop('from_')

        return retval
    


def make_response_msg():
    retval = OC2Msg()
    retval.body.openc2 = OC2RspParent()
    retval.headers.created = int(round(time.time() *1000))
    return retval





if __name__ == "__main__":
    import json
    import pprint
    cmd_json = {}
    with open('/home/vagrant/work/scrap_2020_10/23/yuuki/openc2-yuuki/yuuki/openc2/sample.json') as a_file:
        cmd_json = json.load(a_file)

    msg_cmd = OC2Msg.init_from_dict(cmd_json)
    pp = pprint.PrettyPrinter()

    msg_cmd_dict = msg_cmd.to_dict()
    pp.pprint(msg_cmd_dict)

    print('now a response')
    msg_rsp = OC2Msg()
    msg_rsp.body.openc2 = OC2RspParent()
    print(msg_rsp)
    msg_rsp_dict = msg_rsp.to_dict()

    pp.pprint(msg_rsp_dict)

    something = make_response_msg()
    print(something)

