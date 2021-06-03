from enum import IntEnum
from typing import Optional, Union, List, Dict, Any, Literal

from pydantic import BaseModel, Extra, Field, validator, root_validator, ValidationError


class StatusCode(IntEnum):
    PROCESSING = 102
    OK = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503

    @property
    def text(self):
        mapping = {
            102: 'Processing - an interim OC2Rsp used to inform the Producer that the Consumer has accepted the '
                 'Command but has not yet completed it.',
            200: 'OK - the Command has succeeded.',
            400: 'Bad Request - the Consumer cannot process the Command due to something that is perceived to be a '
                 'Producer error (e.g., malformed Command syntax).',
            401: 'Unauthorized - the Command Message lacks valid authentication credentials for the target resource '
                 'or authorization has been refused for the submitted credentials.',
            403: 'Forbidden - the Consumer understood the Command but refuses to authorize it.',
            404: 'Not Found - the Consumer has not found anything matching the Command.',
            500: 'Internal Error - the Consumer encountered an unexpected condition that prevented it from performing '
                 'the Command.',
            501: 'Not Implemented - the Consumer does not support the functionality required to perform the Command.',
            503: 'Service Unavailable - the Consumer is currently unable to perform the Command due to a temporary '
                 'overloading or maintenance of the Consumer. '
        }
        return mapping[self.value]

    def __repr__(self):
        return str(self.value)


class OC2NfyFields(BaseModel, extra=Extra.forbid, allow_mutation=False):
    pass


class OC2Nfy(BaseModel, extra=Extra.forbid, allow_mutation=False):
    notification: OC2NfyFields


class OC2RspFields(BaseModel, extra=Extra.forbid, allow_mutation=False):
    status: StatusCode
    status_text: Optional[str]
    results: Optional[Dict[str, Any]]

    @validator('status_text', always=True)
    def set_status_text(cls, status_text, values):
        return status_text or values['status'].text


class OC2Rsp(BaseModel, extra=Extra.forbid, allow_mutation=False):
    response: OC2RspFields


class OC2CmdArgs(BaseModel, extra=Extra.allow, allow_mutation=False):
    start_time: Optional[int]
    stop_time: Optional[int]
    duration: Optional[int]
    response_requested: Optional[Literal['none', 'ack', 'status', 'complete']]

    @root_validator
    def check_arg_length(cls, args):
        for arg in args:
            if args[arg] is not None:
                return args
        raise ValueError('Args must have at least one argument if specified')

    @root_validator
    def check_time_args(cls, args):
        if all(args[time_arg] is not None for time_arg in ('start_time', 'stop_time', 'duration')):
            raise ValueError('Can have at most two of [start_time, stop_time, duration]')
        return args

    @root_validator
    def check_extra_args(cls, args):
        for arg in args:
            if arg not in ('start_time', 'stop_time', 'duration', 'response_requested'):
                if type(args[arg]) is not dict:
                    raise ValueError('Value of extra arguments must be a dictionary')
        return args


class OC2CmdFields(BaseModel, extra=Extra.forbid, allow_mutation=False):
    action: str
    target: Dict[str, Any]
    args: Optional[OC2CmdArgs]
    actuator: Optional[Dict[str, Dict[Any, Any]]]
    command_id: Optional[str]

    @validator('target')
    def validate_target_length(cls, target: Dict):
        if len(target) != 1:
            raise ValueError('Target dictionary length must be one')
        return target

    @property
    def target_name(self):
        return next(iter(self.target))


class OC2Cmd(BaseModel, extra=Extra.forbid, allow_mutation=False):
    request: OC2CmdFields


class OC2Headers(BaseModel, extra=Extra.forbid, allow_mutation=False, allow_population_by_field_name=True):
    request_id: Optional[str]
    created: Optional[int]
    from_: Optional[str] = Field(alias='from')
    to: Optional[Union[str, List[str]]]


class OC2Body(BaseModel, extra=Extra.forbid, allow_mutation=False):
    openc2: Union[OC2Cmd, OC2Rsp, OC2Nfy]


class OC2Msg(BaseModel, extra=Extra.forbid, allow_mutation=False):
    headers: OC2Headers
    body: OC2Body
