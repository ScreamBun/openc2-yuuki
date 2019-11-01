from enum import Enum, auto


class ResponseCode(Enum):
    PROCESSING          = 102
    OK                  = 200
    BAD_REQUEST         = 400
    UNAUTHORIZED        = 401
    FORBIDDEN           = 403
    NOT_FOUND           = 404
    INTERNAL_ERROR      = 500
    NOT_IMPLEMENTED     = 501
    SERVICE_UNAVAILABLE = 503
    
    def text(self):
        mapping = {
            102: 'Processing - an interim Response used to inform the Producer that the Consumer has accepted the Command but has not yet completed it.',
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


class Response():
    def __init__(self, response_code = ResponseCode.NOT_IMPLEMENTED,
                       status_text   = None,
                       results       = None):
        self.response_code = response_code
        self.status_text   = status_text
        self._results      = results
    def __repr__(self):
        return self.as_dict().__repr__()
    def as_dict(self):
        retval = {'status'      : self.response_code.value,
                  'status_text' : self.status_text if self.status_text else self.response_code.text()}
        if self._results is not None:
            retval['results'] = self._results
        return retval