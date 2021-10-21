"""
Base class for OpenC2 Command Handlers that you create.
"""

import logging
from functools import partial

from .command_decorators import _OC2PairMeta
from .openc2_types import OpenC2Msg, StatusCode, OpenC2CmdFields, OpenC2RspFields


class OpenC2CmdDispatchBase(metaclass=_OC2PairMeta):
    """Base class to use for your OpenC2 Command Handler.

    This will dispatch received cmds to functions that you tag
    with the decorators in command_util.py.

    validator is any callable that takes a Python dictionary
    of a deserialized command that returns an OpenC2Cmd Object.

    Comes with a built-in handler for query-features you can call.

    For example:

    class MyCommandHandler(OpenC2CmdDispatchBase):
        ...
        @oc2_pair('my_actuator_nsid', 'my_action', 'my_target'):
        def a_function(self, oc2_cmd):
            ...

    The above function will be called when this message arrives off
    the transport:

    action: 'my_actuator_nsid'
    target: {'my_target' : ...}
    actuator: {my_actautor_nsid : {...}}

    See the implementation of get_actuator_callable for details.

    """

    @property
    def rate_limit(self):
        raise NotImplementedError

    @property
    def versions(self):
        raise NotImplementedError

    @property
    def profiles(self):
        raise NotImplementedError

    @property
    def pairs(self):
        pairs = {}
        for func_name in self.oc2_methods:
            func = getattr(self, func_name)
            action = func.action_name
            target = func.target_name
            if action in pairs.keys():
                pairs[action].append(target)
            else:
                pairs[action] = [target]
        return pairs

    def get_actuator_callable(self, oc2_msg: OpenC2Msg):

        logging.debug('Validating...')
        logging.info(f'oc2_msg:\n{oc2_msg}')
        oc2_cmd = oc2_msg.body.openc2.request
        cmd_actuator_nsid = None

        logging.debug('Determining which Consumer/Actuator function to call')
        if isinstance(oc2_cmd.actuator, dict):
            if len(oc2_cmd.actuator.keys()) == 1:
                cmd_actuator_nsid, = oc2_cmd.actuator.keys()

        if oc2_cmd.action == 'query' and oc2_cmd.target_name == 'features':
            func_name = getattr(self, 'oc2_query_features')

        elif (oc2_cmd.action in self.oc2_methods_dict.keys() and
              oc2_cmd.target_name in self.oc2_methods_dict[oc2_cmd.action].keys()):

            if cmd_actuator_nsid is None:
                # Grab the first matching action-target pair. 
                # Behavior of duplicate action-target pair functions (and their response(s))
                # is undefined in the OpenC2 language, so we don't try to solve that here,
                # and instead just call the first matching function

                first_actuator_nsid, = self.oc2_methods_dict[oc2_cmd.action][oc2_cmd.target_name].keys()
                func_name = self.oc2_methods_dict[oc2_cmd.action][oc2_cmd.target_name][first_actuator_nsid]

            else:
                if cmd_actuator_nsid in self.oc2_methods_dict[oc2_cmd.action][oc2_cmd.target_name].keys():
                    func_name = self.oc2_methods_dict[oc2_cmd.action][oc2_cmd.target_name][cmd_actuator_nsid]

                else:
                    func_name = getattr(self, 'oc2_no_matching_nsid')

        else:
            func_name = getattr(self, 'oc2_no_matching_pair')

        if func_name is not None:
            func = getattr(self, func_name)
        else:
            raise NotImplementedError('No function defined for: ', oc2_cmd)

        logging.debug(f'Will call a method named: {func_name}')
        my_callable = partial(func, oc2_cmd)
        return my_callable

    def query_features(self, oc2_cmd: OpenC2CmdFields):
        """
        https://docs.oasis-open.org/openc2/oc2ls/v1.0/cs02/oc2ls-v1.0-cs02.html#41-implementation-of-query-features-command
        """
        logging.debug('Using base implementation of query-features')

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
