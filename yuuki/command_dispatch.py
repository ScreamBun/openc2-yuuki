"""OpenC2 Command Handler

This will dispatch received commands to functions that are tagged with the openc2_pair decorator.

Comes with a built-in handler for query-features.

Example:

my_dispatch = OpenC2Dispatch(rate_limit=60, versions=['1.0']):
    ...
    @my_dispatch.openc2_pair('my_action', 'my_target', 'my_actuator_nsid'):
    def a_function(self, oc2_cmd):
        ...

The above function will be called when this message arrives off
the transport:

action: 'my_action'
target: {'my_target' : ...}
actuator: {my_actautor_nsid : {...}}

"""
import logging
from functools import partial
from collections import defaultdict
from typing import Callable, Dict, List, DefaultDict

from .openc2_types import OpenC2Msg, StatusCode, OpenC2CmdFields, OpenC2RspFields


class OpenC2Dispatch:

    def __init__(self, rate_limit: int, versions: List[str]):
        self.dispatch: DefaultDict[str: DefaultDict[str: Dict[str: Callable]]] = defaultdict(lambda: defaultdict(dict))
        self.pairs: DefaultDict[str, List[str]] = defaultdict(list)
        self.pairs['query'].append('features')
        self.profiles: List[str] = []
        self.rate_limit: int = rate_limit
        self.versions: List[str] = versions

    def get_actuator_callable(self, oc2_msg: OpenC2Msg) -> Callable:
        """Identifies the appropriate function to perform the received OpenC2 command

        :param oc2_msg: the OpenC2 message received by the consumer

        :return: the function with the received OpenC2 command supplied as an argument
        """

        logging.debug('Validating...')
        logging.info(f'oc2_msg:\n{oc2_msg}')
        logging.debug('Determining which Consumer/Actuator function to call')

        oc2_cmd = oc2_msg.body.openc2.request

        if oc2_cmd.action == 'query' and oc2_cmd.target_name == 'features':
            func = self.query_features
        elif oc2_cmd.action in self.dispatch and oc2_cmd.target_name in self.dispatch[oc2_cmd.action]:
            if oc2_cmd.actuator_name is None:
                # Behavior of duplicate action-target pair functions (and their response(s))
                # is undefined in the OpenC2 language, so we don't try to solve that here,
                # and instead just call the first matching function
                func = next(iter(self.dispatch[oc2_cmd.action][oc2_cmd.target_name].values()))
            else:
                if oc2_cmd.actuator_name in self.dispatch[oc2_cmd.action][oc2_cmd.target_name]:
                    func = self.dispatch[oc2_cmd.action][oc2_cmd.target_name][oc2_cmd.actuator_name]
                else:
                    raise TypeError(f'No actuator: {oc2_cmd.actuator_name}')
        else:
            raise TypeError(f'No action-target pair for {oc2_cmd.action} {oc2_cmd.target_name}')

        logging.debug(f'Will call a function named: {func.__name__}')
        return partial(func, oc2_cmd)

    def query_features(self, oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
        """
        https://docs.oasis-open.org/openc2/oc2ls/v1.0/cs02/oc2ls-v1.0-cs02.html#41-implementation-of-query-features-command
        """

        if oc2_cmd.args is not None:
            if oc2_cmd.args.dict(exclude_unset=True).keys() != {'response_requested'}:
                return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Only arg response_requested allowed')

            if oc2_cmd.args.response_requested != 'complete':
                return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                                       status_text='Only arg response_requested=complete allowed')

        target_specifiers = {'versions', 'profiles', 'pairs', 'rate_limit'}
        features: list[str] = oc2_cmd.target['features']

        if not set(features).issubset(target_specifiers):
            return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                                   status_text='features field only allows versions, profiles, rate_limit, and pairs')

        results = {}
        for target_specifier in target_specifiers:
            if target_specifier in features:
                results[target_specifier] = getattr(self, target_specifier)

        if len(results) > 0:
            return OpenC2RspFields(status=StatusCode.OK, results=results)
        else:
            return OpenC2RspFields(status=StatusCode.OK)

    def openc2_pair(self, action: str, target: str, actuator_nsid: str) -> Callable:
        """Decorator for Consumer/Actuator functions.

        Example:

        my_dispatch = OpenC2Dispatch(rate_limit=60, versions=['1.0']):
            ...
            @my_dispatch.openc2_pair('slpf', 'deny', 'ipv4_connection')
            def some_function(oc2_cmd):
                return OpenC2RspFields()
        """
        def decorator(function: Callable) -> Callable:
            self.register_pair(function, action, target, actuator_nsid)
            return function
        return decorator

    def register_pair(self, function: Callable, action: str, target: str, actuator_nsid: str) -> None:
        """Adds function to the dispatch dictionary and the dictionary of action-target pairs.
        Adds actuator_nsid to the list of supported actuator profiles if the list does not already contain it.

        :param function: the function to be called when the consumer receives a command matching the corresponding
            action, target, and actuator_nsid.
        :param action: name of the action to be performed by the function
        :param target: name of the object of the action
        :param actuator_nsid: NSID of the actuator profile that the action-target pair belongs to
        """
        self.dispatch[action][target][actuator_nsid] = function
        self.pairs[action].append(target)
        if actuator_nsid not in self.profiles:
            self.profiles.append(actuator_nsid)
