from ..common.response import Response, ResponseCode
from ..common.util import OC2Cmd
from .decorators import target


profile_registry = {
    'NSID'        : 'x-acme',
    'VERSIONS'    : ['1.0'],
    'PAIRS'       : [] # Auto-populated with action-target pairs below.
}


@target('x-acme:road_runner')
def locate(cmd : OC2Cmd):
    """
    """
    return Response(response_code = ResponseCode.OK, 
                    status_text   = f'Road Runner has been located!')


@target('x-acme:road_runner')
def detonate(cmd : OC2Cmd):
    """
    """
    return Response(response_code = ResponseCode.INTERNAL_ERROR, 
                    status_text   = f'INTERNAL ERROR! Now targetting Coyote!!')

@target('properties')
def set(cmd : OC2Cmd):
    """
    """
    return Response(response_code = ResponseCode.OK, 
                    status_text   = f'set properties got {cmd}')

@target('device')
def restart(cmd : OC2Cmd):
    """
    """
    return Response(response_code = ResponseCode.OK, 
                    status_text   = f'restart device got {cmd}')


@target('device')
def start(cmd : OC2Cmd):
    """
    """
    return Response(response_code = ResponseCode.OK, 
                    status_text   = f'start device got {cmd}')

@target('device')
def stop(cmd : OC2Cmd):
    """
    """
    return Response(response_code = ResponseCode.OK, 
                    status_text   = f'stop device got {cmd}')