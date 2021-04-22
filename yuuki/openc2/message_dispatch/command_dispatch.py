"""
Base class for OpenC2 Command Handlers that you create.
"""

from functools import partial
import logging
from .command_decorators import _OC2PairMeta
from ..oc2_types import OC2Cmd, OC2Rsp, OC2Msg, StatusCode


class OpenC2CmdDispatchBase(metaclass=_OC2PairMeta):
    """Base class to use for your OpenC2 Command Handler.

    This will dispatch received cmds to functions that you tag
    with the decorators in command_util.py.

    validator is any callable that takes a Python dictionary
    of a deserialized command that returns an OC2Cmd Object.

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

    def __init__(self, validator):
        """ validator is any callable that takes a Python dictionary,
        that returns an OC2Cmd Object.
        """
        self.validator = validator

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

    def get_actuator_callable(self, oc2_msg: OC2Msg):

        logging.debug('Validating...')
        logging.info(f'oc2_msg:\n{oc2_msg}')
        # oc2_cmd = self.validator(oc2_msg)
        oc2_cmd = oc2_msg.body.openc2.request
        cmd_actuator_nsid = None

        logging.debug('Determining which Consumer/Actuator function to call')
        if isinstance(oc2_cmd.actuator, dict):
            if len(oc2_cmd.actuator.keys()) == 1:
                cmd_actuator_nsid, = oc2_cmd.actuator.keys()

        cmd_action = oc2_cmd.action
        cmd_target = oc2_cmd.target_name

        if cmd_action == 'query' and cmd_target == 'features':
            func_name = getattr(self, 'oc2_query_features')

        elif (cmd_action in self.oc2_methods_dict.keys() and
              cmd_target in self.oc2_methods_dict[cmd_action].keys()):

            if cmd_actuator_nsid is None:
                # Grab the first matching action-target pair. 
                # Behavior of duplicate action-target pair functions (and their response(s))
                # is undefined in the OpenC2 language, so we don't try to solve that here,
                # and instead just call the first matching function

                first_actuator_nsid, = self.oc2_methods_dict[cmd_action][cmd_target].keys()
                func_name = self.oc2_methods_dict[cmd_action][cmd_target][first_actuator_nsid]

            else:
                if cmd_actuator_nsid in self.oc2_methods_dict[cmd_action][cmd_target].keys():
                    func_name = self.oc2_methods_dict[cmd_action][cmd_target][cmd_actuator_nsid]

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

    def query_features(self, oc2_cmd: OC2Cmd):
        """
        https://docs.oasis-open.org/openc2/oc2ls/v1.0/cs02/oc2ls-v1.0-cs02.html#41-implementation-of-query-features-command
        """
        logging.debug('Using base implementation of query-features')
        # Arguments
        args_response_requested = None
        args_other = None

        if oc2_cmd.args is not None:
            for key, value in oc2_cmd.args.items():
                if key == 'response_requested':
                    args_response_requested = value
                else:
                    args_other = str(args_other) + str(key) + str(value)

        if args_response_requested is not None and args_response_requested != 'complete':
            return OC2Rsp(status=StatusCode.BAD_REQUEST,
                          status_text='Only arg response_requested=complete allowed')
        if args_other is not None:
            return OC2Rsp(status=StatusCode.BAD_REQUEST,
                          status_text='Only arg response_requested allowed')

        # Target Specifiers

        retval_results = {}

        for item in oc2_cmd.target['features']:
            if item == 'versions':
                retval_results['versions'] = self.versions
            elif item == 'profiles':
                retval_results['profiles'] = self.profiles
            elif item == 'rate_limit':
                retval_results['rate_limit'] = self.rate_limit
            elif item == 'pairs':
                retval_results['pairs'] = self.pairs
            else:
                return OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text='features field only allows versions, profiles, rate_limit, and pairs')

        if len(retval_results) > 0:
            return OC2Rsp(status=StatusCode.OK,
                          results=retval_results)
        else:
            return OC2Rsp(status=StatusCode.OK)
