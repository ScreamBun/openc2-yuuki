from ..common.util import Pair


class _Target():
    """Store a real function to be called later, with its target name.
    """
    def __init__(self, name, function):
        self.name = name
        self.function = function

class _Action():
    """Contain all the functions of the same name in a profile, e.g.'deny'.

    For example, could contain the two functions for 'deny mac_addr' and 
    'deny domain_name'. When an instance of this class is called, it will
    look up which function to call based on the target (mac_addr, etc)
    given in the call args. 
    """
    def __init__(self, name):
        self.name = name
        self._targets = {}
    
    def pair(self, target_obj : _Target):
        if target_obj.name in self._targets:
            raise ValueError(f'Target ({target_obj.name}) already paired with Action ({self.name})')
        self._targets[target_obj.name] = target_obj

    def __call__(self, cmd):
        target_name, = cmd.target.keys()
        if target_name not in self._targets:
            raise ValueError(f'Target ({target_name}) not paired with Action ({self.name})')
        
        function_to_call = self._targets[target_name].function

        return function_to_call(cmd)


def target(target_name):
    """ Decorator - Very similiar to functools.singledispatch.

    But instead of dispatching on a TYPE of argument, we dispatch
    on the VALUE of an argument attribute (cmd.target, e.g. 'domain_name').
    """

    def _register(action_function):
        """Instantiates a wrapper object (_Action) to store the 
        action_function in a lookup table, and adds any subsequent functions
        of the same name to the same wrapper object. Also updates the
        profile_registry with the action-target pairs encountered.
        """
        action_name = action_function.__name__
        
        action_obj  = action_function.__globals__.get(action_name)

        if action_obj is None:
            action_obj = _Action(action_name)
        
        # This function is the easiest place to gather info for
        # the profile_registry
        profile_registry = action_function.__globals__.get('profile_registry')
        registered_pairs = profile_registry['PAIRS']

        pair = Pair(action_name, target_name)
        if pair in registered_pairs:
            raise ValueError(f'How did this happen...')
        registered_pairs.append(pair)

        # Now actually store the action function with its target name, etc...
        target_obj = _Target(target_name, action_function)
        action_obj.pair(target_obj)

        return action_obj
            
    return _register