"""OpenC2 Types
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html

For validating and parsing OpenC2 Messages
"""
from enum import IntEnum
from typing import Optional, Union, List, Dict, Any, Literal

from pydantic import BaseModel, Extra, Field, validator, root_validator


class StatusCode(IntEnum):
    """
    https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#3321-response-status-code
    """
    PROCESSING = 102
    OK = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503

    def __repr__(self):
        return str(self.value)


class OpenC2NtfFields(BaseModel, extra=Extra.forbid):
    pass


class OpenC2Ntf(BaseModel, extra=Extra.forbid):
    notification: OpenC2NtfFields


class OpenC2RspFields(BaseModel, extra=Extra.forbid):
    """
    https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#332-openc2-response
    """
    status: StatusCode
    status_text: Optional[str]
    results: Optional[Dict[str, Any]]


class OpenC2Rsp(BaseModel, extra=Extra.forbid):
    response: OpenC2RspFields


class OpenC2CmdArgs(BaseModel, extra=Extra.allow):
    """
    https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#3314-command-arguments
    """
    start_time: Optional[int]
    stop_time: Optional[int]
    duration: Optional[int]
    response_requested: Optional[Literal['none', 'ack', 'status', 'complete']]

    @root_validator
    def check_arg_length(cls, args):
        for value in args.values():
            if value is not None:
                return args
        raise ValueError('Args must have at least one argument if specified')

    @root_validator
    def check_time_args(cls, args):
        if all(args.get(time_arg) is not None for time_arg in ('start_time', 'stop_time', 'duration')):
            raise ValueError('Can have at most two of [start_time, stop_time, duration]')
        return args

    @root_validator
    def check_extra_args(cls, args):
        for arg, value in args.items():
            if arg not in ('start_time', 'stop_time', 'duration', 'response_requested'):
                if type(value) is not dict:
                    raise ValueError('Value of extra arguments must be a dictionary')
        return args


class OpenC2CmdFields(BaseModel, extra=Extra.forbid):
    """
    https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#331-openc2-command
    """
    action: str
    target: Dict[str, Any]
    args: Optional[OpenC2CmdArgs]
    actuator: Optional[Dict[str, Dict[Any, Any]]]
    command_id: Optional[str]

    @validator('target', 'actuator')
    def validate_choice_length(cls, choice: Dict):
        if len(choice) != 1:
            raise ValueError('Choice fields must have a length of one')
        return choice

    @property
    def target_name(self):
        return next(iter(self.target))

    @property
    def actuator_name(self):
        if self.actuator is None:
            return None
        else:
            return next(iter(self.actuator))


class OpenC2Cmd(BaseModel, extra=Extra.forbid):
    request: OpenC2CmdFields


class OpenC2Headers(BaseModel, extra=Extra.forbid, allow_population_by_field_name=True):
    request_id: Optional[str]
    created: Optional[int]
    from_: Optional[str] = Field(alias='from')
    to: Optional[Union[str, List[str]]]


class OpenC2Body(BaseModel, extra=Extra.forbid):
    openc2: Union[OpenC2Cmd, OpenC2Rsp, OpenC2Ntf]


class OpenC2Msg(BaseModel, extra=Extra.forbid):
    """
    https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#32-message
    """
    headers: Optional[OpenC2Headers]
    body: OpenC2Body

    @root_validator
    def set_command_id(cls, fields):
        """
        See 'Usage Requirements' under:
        https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#331-openc2-command
        """
        if isinstance(fields['body'].openc2, OpenC2Cmd):
            if fields['headers'] is not None and fields['headers'].request_id is not None:
                if fields['body'].openc2.request.command_id is None:
                    fields['body'].openc2.request.command_id = fields['headers'].request_id
        return fields
