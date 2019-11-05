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
    return Response(status = ResponseCode.OK, 
                    status_text = f'Road Runner has been located!')

@target('x-acme:road_runner')
def detonate(cmd : OC2Cmd):
    return Response(status = ResponseCode.INTERNAL_ERROR, 
                    status_text = f'INTERNAL ERROR! Now targetting Coyote!!')

@target('properties')
def set(cmd : OC2Cmd):
    return Response(status = ResponseCode.OK, 
                    status_text = f'Properties have been set.')

@target('device')
def restart(cmd : OC2Cmd):
    return Response(status = ResponseCode.OK, 
                    status_text = f'Device has been restarted')

@target('device')
def start(cmd : OC2Cmd):
    return Response(status = ResponseCode.OK, 
                    status_text = f'Device is started')

@target('device')
def stop(cmd : OC2Cmd):
    return Response(status = ResponseCode.OK, 
                    status_text = f'Device has been stopped')