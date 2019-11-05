from ..common.response import Response, ResponseCode
from ..common.util import OC2Cmd
from .decorators import target


profile_registry = {
    'NSID'        : 'x-music',
    'VERSIONS'    : ['1.0'],
    'PAIRS'       : [] # Auto-populated
}


@target('x-music:song')
def start(cmd : OC2Cmd):
    return Response(status = ResponseCode.OK, 
                    status_text = f'Started a song...')

@target('x-music:song')
def stop(cmd : OC2Cmd):
    return Response(status = ResponseCode.OK, 
                    status_text = f'Stopped a song...')

