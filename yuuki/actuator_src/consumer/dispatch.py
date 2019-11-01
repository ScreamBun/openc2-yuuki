from .validate import convert_raw_cmd
from ..common.response import ResponseCode, Response
from ..common.util import OC2Cmd, Pair, OC2Exception
from .. import profiles


class Dispatcher():
    """
    """

    def dispatch(self, raw_cmd : dict):
        """Receive a command; dispatch to a profile module based on pair.
        """
        
        try:
            cmd = convert_raw_cmd(raw_cmd)
        except OC2Exception as e:
            return Response(response_code=ResponseCode.BAD_REQUEST,
                            status_text=str(e))

        action  = cmd.action
        target, = cmd.target.keys()
        pair    = Pair(action, target)
        
        try:
            retval = profiles.do_it(pair, cmd)
        except Exception as e:
            return Response(response_code=ResponseCode.NOT_FOUND, status_text=str(e))

        return retval