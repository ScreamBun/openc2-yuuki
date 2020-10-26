"""Basic OpenC2 Types: Command, Response, etc"""

from enum import Enum
from collections import UserDict, namedtuple
from typing import Optional, List, Dict
import json

OC2Cmd = namedtuple('OC2Cmd', 'action target target_name args actuator command_id')
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



class OC2Rsp():
    def __init__(self,
                 status: StatusCode = StatusCode.NOT_IMPLEMENTED,
                 status_text: Optional[str] = None,
                 results: Optional[Dict[str,str]] = None):
        self._status = status
        self._status_text = status_text
        self._results = results
    
    @property
    def status(self):
        return self._status.value
    @property
    def status_text(self):
        return self._status_text
    @property
    def results(self):
        return self._results

    @property
    def keys_for_serializing(self):
        retval = ['status']
        if self._status_text is not None:
            retval.append('status_text')
        if self._results is not None:
            retval.append('results')
        return retval