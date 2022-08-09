"""
OpenC2 Response Types
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html

For validating and parsing OpenC2 Messages
"""
import json
from enum import IntEnum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Extra


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


class OpenC2RspFields(BaseModel, extra=Extra.forbid):
    """
    https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#332-openc2-response
    """
    status: StatusCode
    status_text: Optional[str]
    results: Optional[Dict[str, Any]]


class OpenC2Rsp(BaseModel, extra=Extra.forbid):
    response: OpenC2RspFields

