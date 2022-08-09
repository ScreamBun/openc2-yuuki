"""
OpenC2 Notification Types
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html

For validating and parsing OpenC2 Messages
"""
from pydantic import BaseModel, Extra


class OpenC2NtfFields(BaseModel, extra=Extra.forbid):
    pass


class OpenC2Ntf(BaseModel, extra=Extra.forbid):
    notification: OpenC2NtfFields
