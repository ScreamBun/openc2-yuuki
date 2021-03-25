"""Decorators for your Consumer/Actuator functions."""

def oc2_pair(actuator_nsid, action_name, target_name):
    """Decorator for your Consumer/Actuator functions.

    Use on functions you implement when inheriting
    from OpenC2CmdDispatchBase.

    Example:

    class MyDispatch(OpenC2CmdDispatchBase):
        ...
        @oc2_pair('slpf', 'deny', 'ipv4_connection')
        def some_function(oc2_cmd):
            return OC2Rsp()
    """
    def _register(method):
        method.is_oc2_pair = True
        method.actuator_nsid = actuator_nsid
        method.action_name = action_name
        method.target_name = target_name
        return method
    return _register

def oc2_no_matching_pair(method):
    """One-use-only decorator

    Use on one function you implement when inheriting
    from OpenC2CmdDispatchBase.

    Will be called when no function is found
    tagged with oc2_pair with a matching action/target
    pair.

    Example:

    class MyDispatch(OpenC2CmdDispatchBase):
        ...
        @oc2_no_matching_pair
        def some_function(oc2_cmd):
            print('we dont support that action-target pair!')
    """

    method.oc2_no_matching_pair = True
    return method

def oc2_no_matching_actuator(method):
    """One-use-only decorator

    Use on one function you implement when inheriting
    from OpenC2CmdDispatchBase.

    Will be called if we DID find a matching action-target pair,
    but not one with the specified actuator nsid.

    Example:

    class MyDispatch(OpenC2CmdDispatchBase):
        ...
        @oc2_no_matching_actuator
        def some_function(oc2_cmd):
            print('we dont support that actuator!')
    """
    method.oc2_no_matching_nsid = True
    return method

def oc2_query_features(method):
    """One-use-only decorator

    Use on one function you implement when inheriting
    from OpenC2CmdDispatchBase.

    Will be called when we receive query-features command

    Example:

    class MyDispatch(OpenC2CmdDispatchBase):
        ...
        @oc2_query_features
        def some_function(oc2_cmd):
            ...
    """
    method.oc2_query_features = True
    return method



class _OC2PairMeta(type):
    """Metaclass helper to make use of our decorators."""
    
    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        class OC2MethodGrabber(dict):
            def __init__(self):
                self.oc2_methods_dict = {}
                self.oc2_methods = []
                self.oc2_no_matching_pair = None
                self.oc2_no_matching_nsid = None
                self.oc2_query_features = None

            def __setitem__(self, key, value):
                if hasattr(value, 'is_oc2_pair'):
                    self.oc2_methods.append(key)
                    actuator_nsid = value.actuator_nsid
                    action = value.action_name
                    target = value.target_name

                    if action not in self.oc2_methods_dict.keys():
                        self.oc2_methods_dict[action] = {target : {actuator_nsid: key}}
                    elif target not in self.oc2_methods_dict[action].keys():
                        self.oc2_methods_dict[action][target] = {actuator_nsid: key}
                    elif actuator_nsid not in self.oc2_methods_dict[action][target].keys():
                        self.oc2_methods_dict[action][target][actuator_nsid] = key
                    else:
                        raise KeyError('Already defined', action, target, actuator_nsid)
                    
                if self.oc2_no_matching_pair is None:
                    if hasattr(value, 'oc2_no_matching_pair'):
                        self.oc2_no_matching_pair = key
                if self.oc2_no_matching_nsid is None:
                    if hasattr(value, 'oc2_no_matching_nsid'):
                        self.oc2_no_matching_nsid = key
                if self.oc2_query_features is None:
                    if hasattr(value, 'oc2_query_features'):
                        self.oc2_query_features = key


                dict.__setitem__(self, key, value)

        return OC2MethodGrabber()
    
    def __new__(cls, name, bases, classdict):
        retval = super().__new__(cls, name, bases, dict(classdict))
        retval.oc2_methods = classdict.oc2_methods
        retval.oc2_no_matching_pair = classdict.oc2_no_matching_pair
        retval.oc2_no_matching_nsid = classdict.oc2_no_matching_nsid
        retval.oc2_methods_dict = classdict.oc2_methods_dict
        retval.oc2_query_features = classdict.oc2_query_features
        return retval