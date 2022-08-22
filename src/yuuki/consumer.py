"""OpenC2 Consumer
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#54-conformance-clause-4-consumer
"""
import json
import logging
from time import time
from pprint import pformat  # properly prints JSON serielized text as part of return messages, useful for SBOM etc
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, Dict, List, Union

from pydantic import ValidationError

from .openc2_types import OpenC2Msg, OpenC2Headers, OpenC2Body, OpenC2Rsp, OpenC2CmdFields, OpenC2RspFields, StatusCode
from .actuator import Actuator
from .serialization import Serialization


class Consumer:
    """
    Processes OpenC2 Commands and issues OpenC2 Responses
    The base Consumer supports the 'query features' OpenC2 Command and JSON serialization.
    """
    dispatch: Dict[str, Dict[str, Dict[str, Callable]]]
    pairs: Dict[str, List[str]]
    understood: Dict[str, List[str]]
    profiles: List[str]
    rate_limit: int
    versions: List[str]
    serializations: Dict[str, Serialization]

    def __init__(self, rate_limit: int, versions: List[str], actuators: List[Actuator] = None, serializations: List[Serialization] = None):
        """
        :param rate_limit: Maximum number of requests per minute supported by design or policy.
        :param versions: List of OpenC2 language versions supported.
        :param actuators: List of Actuators to be added to the Consumer.
        :param serializations: List of serializations to be added to the Consumer.
        """
        self.dispatch = {}
        self.pairs = {
            'query': ['features']
        }
        self.understood = {
            'query': ['features']
        }
        self.profiles = []
        self.rate_limit = rate_limit
        self.versions = versions
        self.serializations = {}
        self.add_serialization(Serialization(name='json', deserialize=json.loads, serialize=json.dumps))
        if serializations is not None:
            for serialization in serializations:
                self.add_serialization(serialization)
        if actuators is not None:
            for actuator in actuators:
                self.add_actuator(actuator)
                print("Added actuator "+actuator.nsid)
        self.executor = ThreadPoolExecutor()
        print(r'''
        _____.___.            __   .__ 
        \__  |   |__ __ __ __|  | _|__|
         /   |   |  |  \  |  \  |/ /  |
         \____   |  |  /  |  /    <|  |
         / ______|____/|____/|__|_ \__|
         \/                       \/   
        ''')

    def process_command(self, command, encode: str) -> Union[str, bytes, None]:
        """
        Processes an OpenC2 Command and return an OpenC2 Response.
        :param command: The OpenC2 Command.
        :param encode: String specifying the serialization format for the Command/Response.
        :return: Serialized OpenC2 Response, or None if no Response was requested by the Command.
        """
        try:
            message = self.serializations[encode].deserialize(command)
        except KeyError:
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                                         status_text='Unsupported serialization protocol')
            return self.create_response_msg(openc2_rsp, encode='json')
        except Exception as e:
            logging.exception('Deserialization failed')
            logging.error(e)
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Deserialization failed')
            return self.create_response_msg(openc2_rsp, encode=encode)

        logging.info(f'Received Command:\n{pformat(message)}')

        try:
            openc2_msg = OpenC2Msg(**message)
        except ValidationError as e:
            #logging.error(e)
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed OpenC2 message')
            return self.create_response_msg(openc2_rsp, encode=encode)
        except KeyError as e:
            #logging.error(e)
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed OpenC2 message')
            return self.create_response_msg(openc2_rsp, encode=encode)

        try:
            actuator_callable = self._get_actuator_callable(openc2_msg)
        except TypeError as e:
            #logging.error(e)
            #sorting logic to differentiate the unknown actuator commmands from known but unimplemented ones
            if openc2_msg.body.openc2.request.action in self.understood \
                    and openc2_msg.body.openc2.request.target_name in self.understood:
                openc2_rsp = OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text='Command Not Supported')
                return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode=encode)
            else:
                openc2_rsp = OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text='No matching Actuator found')
                return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode=encode)

        if openc2_msg.body.openc2.request.args:
            if response_requested := getattr(openc2_msg.body.openc2.request.args, "response_requested", 'complete'):
                if response_requested == 'none':
                    self.executor.submit(actuator_callable)
                    return None
                elif response_requested == 'ack':
                    self.executor.submit(actuator_callable)
                    return self.create_response_msg(OpenC2RspFields(status=StatusCode.PROCESSING),
                                                    headers=openc2_msg.headers, encode=encode)
                elif response_requested == 'status':
                    pass
                elif response_requested == 'complete':
                    pass
        else:
            pass

        try:
            openc2_rsp = actuator_callable()
        except NotImplementedError:
            openc2_rsp = OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text='Command not supported')
            return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode=encode)
        except Exception as e:
            logging.exception('Actuator failed')
            logging.error(e)
            openc2_rsp = OpenC2RspFields(status=StatusCode.INTERNAL_ERROR, status_text='Actuator failed')
            return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode=encode)

        try:
            return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode=encode)
        except Exception as e:
            logging.exception('Serialization error occurred')
            logging.error(e)
            openc2_rsp = OpenC2RspFields(status=StatusCode.INTERNAL_ERROR, status_text='Serialization failed')
            return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode='json')

    def create_response_msg(self, response_body,  encode: str, headers: OpenC2Headers = None) -> Union[str, bytes]:
        """
        Creates and serializes an OpenC2 Response.
        :param response_body: Information to populate OpenC2 Response fields.
        :param headers: Information to populate OpenC2 Response headers.
        :param encode: String specifying the serialization format for the Response.
        :return: Serialized OpenC2 Response
        """
        print("creating response")

        if headers is None:
            # print("debugging: no headers")
            headers = OpenC2Headers(from_="Yuuki")

        else:
            # print("debugging: found headers")
            headers = OpenC2Headers(
                request_id=headers.request_id,
                from_="Yuuki",
                to=headers.from_,
                created=round(time() * 1000)
            )

        message = OpenC2Msg(headers=headers, body=OpenC2Body(openc2=OpenC2Rsp(response=response_body)))
        response = message.dict(by_alias=True, exclude_unset=True, exclude_none=True)
        logging.info(f'Response:\n{pformat(response)}')
        print("debugging: response on the way")
        return self.serializations[encode].serialize(response)

    def _get_actuator_callable(self, oc2_msg: OpenC2Msg) -> Callable[[], OpenC2RspFields]:
        """
        Identifies the appropriate function to perform the received OpenC2 Command.
        :param oc2_msg: The OpenC2 Message received by the Consumer.
        :return: The function with the received OpenC2 Command supplied as an argument.
        """
        oc2_cmd = oc2_msg.body.openc2.request
        print(f"{oc2_cmd.action} {oc2_cmd.target_name} {oc2_cmd.profile_name}")
        print(self.dispatch)
        print(self.understood)
        if oc2_cmd.action == 'query' and oc2_cmd.target_name == 'features':
            function = self.query_features
        elif oc2_cmd.action in self.dispatch and oc2_cmd.target_name in self.dispatch[oc2_cmd.action]:
            if oc2_cmd.profile_name is None:
                # Behavior of duplicate Action-Target pairs is currently undefined in the OpenC2 language.
                # For the time being, this is handled by calling the function of the first matching pair.
                function = next(iter(self.dispatch[oc2_cmd.action][oc2_cmd.target_name].values()))
            else:
                if oc2_cmd.profile_name in self.dispatch[oc2_cmd.action][oc2_cmd.target_name]:
                    function = self.dispatch[oc2_cmd.action][oc2_cmd.target_name][oc2_cmd.profile_name]
                else:
                    raise TypeError(f'No Actuator: {oc2_cmd.profile_name}')
        elif oc2_cmd.action in self.understood and oc2_cmd.target_name in self.understood[oc2_cmd.action]:
            function = self.unimplemented_command_function
        else:
            raise TypeError(f'No Action-Target pair for {oc2_cmd.action} {oc2_cmd.target_name}')

        #logging.debug(f'Will call a function named: {function.__name__}')
        return partial(function, oc2_cmd)

    def query_features(self, oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
        """
        Implementation of the 'query features' Command as described in the OpenC2 Language Specification
        https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#41-implementation-of-query-features-command
        """
        print("query features")
        if oc2_cmd.args is not None:
            if oc2_cmd.args.dict(exclude_unset=True).keys() != {'response_requested'}:
                return OpenC2RspFields(
                    status=StatusCode.BAD_REQUEST,
                    status_text='Only arg response_requested allowed'
                )

            if oc2_cmd.args.response_requested != 'complete':
                return OpenC2RspFields(
                    status=StatusCode.BAD_REQUEST,
                    status_text='Only arg response_requested=complete allowed'
                )

        target_specifiers = {'versions', 'profiles', 'pairs', 'rate_limit'}
        features: List[str] = oc2_cmd.target['features']

        if not set(features).issubset(target_specifiers):
            return OpenC2RspFields(
                status=StatusCode.BAD_REQUEST,
                status_text='features field only allows versions, profiles, rate_limit, and pairs'
            )

        results = {}
        if "pairs" in target_specifiers:
            target_specifiers.remove("pairs")
            results["pairs"] = {k: list(v.keys()) for k, v in self.dispatch.items()}
            results["pairs"].setdefault("query", []).append("features")

        for target_specifier in target_specifiers:
            if target_specifier in features:
                results[target_specifier] = getattr(self, target_specifier)

        if len(results) > 0:
            return OpenC2RspFields(status=StatusCode.OK, results=results)
        else:
            return OpenC2RspFields(status=StatusCode.OK)

    def unimplemented_command_function(self, oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
        """
        Handles instances of get_actuator_callable that find a command that is understood by an profile
        but not implemented by the actuator. Returns OpenC2 RSP with a 501 error.
        """
        print("Command Not Implemented")
        return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text='Command Not Supported')

    def add_actuator(self, actuator: Actuator) -> None:
        """
        Adds the Actuator's functions to the Consumer and adds the Actuator's namespace identifier (nsid) to the
        list of supported profiles
        :param actuator: The Actuator whose functions will be added to the Consumer.
        """
        if actuator.nsid in self.profiles:
            raise ValueError('Actuator with the same nsid already exists')
        else:
            self.profiles.append(actuator.nsid)
            self.pairs.update(actuator.pairs)
            self.understood.update(actuator.understood)
            self._update_dispatch_rec(self.dispatch, actuator.dispatch)

    def add_serialization(self, serialization: Serialization) -> None:
        """
        Adds the serialization to the Consumer, enabling it to serialize and deserialize messages using the
        serialization's methods.
        :param serialization: The serialization to be added to the Consumer.
        """
        self.serializations[serialization.name] = serialization

    def _update_dispatch_rec(self, update: Dict[str, Any], data: Dict[str, Any]) -> None:
        for key, val in data.items():
            if isinstance(val, dict):
                self._update_dispatch_rec(update.setdefault(key, {}), val)
            else:
                update.update({key: val})


