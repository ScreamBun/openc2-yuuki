from importlib import import_module
from ..common.util import OC2Cmd
from ..common.response import Response, ResponseCode

# Set which profile(s) are in use.
ACTIVE_PROFILES = ['profile_acme_anti_roadrunner']

class _ProfileModule():
    def __init__(self, file_name):
        self.NSID = None
        self.file_name = file_name
        self.module = None
        self.PAIRS = []
        self.VERSIONS = None

NSIDS      = []
PAIRS      = {}
VERSIONS   = []
RATE_LIMIT = 30 # Magic!

for profile_name in ACTIVE_PROFILES:
    profile_module = _ProfileModule(profile_name)

    profile_module.module = import_module('.' + profile_name, package='yuuki.actuator_src.profiles')
    
    profile_registry = getattr(profile_module.module,'profile_registry')
    
    profile_module.NSID        = profile_registry['NSID']
    profile_module.PAIRS       = profile_registry['PAIRS'].copy()
    profile_module.VERSIONS    = profile_registry['VERSIONS'].copy()
   
    if profile_module.NSID in NSIDS:
        raise ValueError('Duplicate profile')
    NSIDS.append(profile_module.NSID)

    for pair in profile_module.PAIRS:
        if pair in PAIRS.keys():
            raise ValueError(f'Duplicate action target pair: {pair}')
        PAIRS[pair] = profile_module
    
    if not VERSIONS:
        VERSIONS = sorted(profile_module.VERSIONS.copy())
    else:
        if VERSIONS != sorted(profile_module.VERSIONS):
            raise ValueError(f'The profiles this actuator implements '
                             f'must all support the same version(s).')


def do_it(pair, cmd):
    """Interface to use by external calls.
    """

    # We handle 'query features' here, instead of in an profile module,
    # because a profile module only knows about itself.
    if pair == ('query', 'features'):
        return _handle_query_features(cmd)
    
    if pair not in PAIRS.keys():
        raise ValueError

    func = getattr(PAIRS[pair].module, pair.action)
    return func(cmd)

def _handle_query_features(cmd : OC2Cmd):
    """
    """
    results = {'versions'   : VERSIONS,
               'profiles'   : NSIDS,
               'rate_limit' : RATE_LIMIT,
               'pairs'      : sorted(
                                 sorted(list(PAIRS.keys()),
                                        key=lambda x: x[1]),
                                 key=lambda x: x[0])}
    
    return Response(response_code=ResponseCode.OK, results=results)