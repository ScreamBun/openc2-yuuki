"""OpenC2 Actuator
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html
"""
from collections import defaultdict
from typing import Callable, Dict, List, DefaultDict

from .openc2_types import OpenC2CmdFields, OpenC2RspFields


OpenC2Function = Callable[[OpenC2CmdFields], OpenC2RspFields]


class Actuator:

    def __init__(self, nsid: str):
        self.dispatch: DefaultDict[str: DefaultDict[str: Dict[str: Callable]]] = defaultdict(lambda: defaultdict(dict))
        self.pairs: DefaultDict[str, List[str]] = defaultdict(list)
        self.nsid: str = nsid

    def pair(self, action: str, target: str) -> Callable:
        """Decorator for actuator functions.

        :param action: Name of the action to be performed by the function
        :param target: Name of the target of the action

        Example:

        actuator = Actuator('my_actuator_nsid'):
            ...
            @actuator.pair('my_action', 'my_target'):
            def a_function(oc2_cmd):
                ...

        The above function will be called when this message arrives off
        the transport:

        action: 'my_action'
        target: {'my_target' : ...}
        actuator: {'my_actuator_nsid' : {...}}
        """
        def decorator(function: OpenC2Function) -> OpenC2Function:
            self.register_pair(function, action, target)
            return function
        return decorator

    def register_pair(self, function: OpenC2Function, action: str, target: str) -> None:
        """Adds function to the dispatch dictionary and the dictionary of action-target pairs.

        :param function: The function to be called when the consumer receives a command matching the corresponding
            action, target, and nsid
        :param action: Name of the action to be performed by the function
        :param target: Name of the target of the action
        """
        self.dispatch[action][target][self.nsid] = function
        self.pairs[action].append(target)
