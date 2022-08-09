"""
OpenC2 Message Types
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html

For validating and parsing OpenC2 Messages
"""
from typing import Optional, Union, List
from pydantic import BaseModel, Extra, Field, root_validator
from .request import OpenC2Cmd
from .response import OpenC2Rsp
from .notification import OpenC2Ntf


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
