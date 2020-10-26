import json
import logging
from .base import _Serializer
from ..openc2.oc2_types import OC2Rsp, StatusCode



class Json(_Serializer):
    @staticmethod
    def serialize(obj : OC2Rsp):
        logging.debug('Json Serialize {} {}'.format( type(obj), obj))
        #return json.dumps(obj)
        return _JsonEncoder().encode(obj)

    @staticmethod
    def deserialize(obj):
        logging.debug('Json Deserialize')
        try:
            retval = json.loads(obj)
            if isinstance(retval, str):
                retval = json.loads(retval)
        except Exception as e:
            print('BAD',e)
            raise
        return retval

class _JsonEncoder(json.JSONEncoder):
    def __init__(self):
        super().__init__()
    def default(self, o : OC2Rsp):
        if isinstance(o, StatusCode):
            return o.value
        return json.JSONEncoder.default(self, o)
        