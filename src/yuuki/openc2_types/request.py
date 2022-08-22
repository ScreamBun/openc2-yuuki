"""
OpenC2 Request Types
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html

For validating and parsing OpenC2 Messages
"""
from typing import Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Extra, validator, root_validator


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

    #@root_validator     ---removed for args issuesKC
    #def check_extra_args(cls, args):
      #  for arg, value in args.items():
       #     if arg not in ('start_time', 'stop_time', 'duration', 'response_requested'):
       #         if type(value) is not dict:
        #            raise ValueError('Value of extra arguments must be a dictionary')
        #return args


class OpenC2CmdFields(BaseModel, extra=Extra.forbid):
    """
    https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#331-openc2-command
    """
    action: str
    target: Dict[str, Any]
    args: Optional[Union[OpenC2CmdArgs, Dict[str, Any]]]
    profile: Optional[Dict[str, Dict[str, Any]]]
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
    def profile_name(self):
        if self.profile is None:
            return None
        else:
            return next(iter(self.profile))


class OpenC2Cmd(BaseModel, extra=Extra.forbid):
    request: OpenC2CmdFields
