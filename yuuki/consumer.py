"""OpenC2 Consumer
https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#54-conformance-clause-4-consumer
"""
import json
import logging
from time import time
from abc import ABC, abstractmethod
from pprint import pformat
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from collections import defaultdict
from typing import Union, Callable, Dict, List, DefaultDict

from pydantic import ValidationError

from .openc2_types import OpenC2Msg, OpenC2Headers, OpenC2Body, OpenC2Rsp, OpenC2CmdFields, OpenC2RspFields, StatusCode
from .actuator import Actuator
from .serialization import Serialization


class Consumer(ABC):
    """Provides the ability to process OpenC2 Commands and issue OpenC2 Responses
    The base Consumer supports the 'query features' OpenC2 Command and JSON serialization.
    OpenC2 Message transfer functionality is achieved by inheriting from this class and implementing the capability to
    send a receive messages using a particular transfer protocol in the child class.
    """

    def __init__(
            self,
            rate_limit: int,
            versions: List[str],
            transport_config,
            actuators: List[Actuator] = None,
            serializations: List[Serialization] = None
    ):
        """
        :param rate_limit: Maximum number of Commands per minute supported by design or policy.
        :param versions: List of OpenC2 language versions supported.
        :param transport_config: Transport-specific configuration.
        :param actuators: List of actuators to be added to the Consumer.
        :param serializations: List of serializations to be added to the Consumer.
        """
        self.dispatch: DefaultDict[str: DefaultDict[str: Dict[str: Callable]]] = defaultdict(lambda: defaultdict(dict))
        self.pairs: DefaultDict[str, List[str]] = defaultdict(list)
        self.pairs['query'].append('features')
        self.profiles: List[str] = []
        self.rate_limit: int = rate_limit
        self.versions: List[str] = versions
        self.serializations: Dict[str, Serialization] = {}
        self.add_serialization(Serialization(name='json', deserialize=json.loads, serialize=json.dumps))
        if serializations is not None:
            for serialization in serializations:
                self.add_serialization(serialization)
        if actuators is not None:
            for actuator in actuators:
                self.add_actuator_profile(actuator)
        self.config = transport_config
        self.executor = ThreadPoolExecutor()
        print(r'''
        _____.___.            __   .__ 
        \__  |   |__ __ __ __|  | _|__|
         /   |   |  |  \  |  \  |/ /  |
         \____   |  |  /  |  /    <|  |
         / ______|____/|____/|__|_ \__|
         \/                       \/   
        ''')

    @abstractmethod
    def start(self):
        """Runs the consumer after configuration steps are complete."""
        raise NotImplementedError

    def process_command(self, raw_data, encode: str) -> Union[str, bytes, None]:
        """Processes commands received from transport then returns a response for the transport to send.

        :param raw_data: The OpenC2 command as received by the transport.
        :param encode: String specifying the serialization format for the command/response.

        :return: Serialized OpenC2 response, or None if no response was requested by the command.
        """
        try:
            message = self.serializations[encode].deserialize(raw_data)
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
        except ValidationError:
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed OpenC2 message')
            return self.create_response_msg(openc2_rsp, encode=encode)

        try:
            actuator_callable = self.get_actuator_callable(openc2_msg)
        except TypeError:
            openc2_rsp = OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text='No matching actuator found')
            return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode=encode)

        if openc2_msg.body.openc2.request.args and openc2_msg.body.openc2.request.args.response_requested:
            response_requested = openc2_msg.body.openc2.request.args.response_requested
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
            logging.exception('Serialization failed')
            logging.error(e)
            openc2_rsp = OpenC2RspFields(status=StatusCode.INTERNAL_ERROR, status_text='Serialization failed')
            return self.create_response_msg(openc2_rsp, headers=openc2_msg.headers, encode='json')

    def create_response_msg(self, response_body: OpenC2RspFields, headers: OpenC2Headers = OpenC2Headers(),
                            encode: str = None) -> Union[str, bytes]:
        """
        Creates and serializes the OpenC2 response to be returned to the transport

        :param response_body: Information to populate OpenC2 response fields.
        :param headers: Information to populate OpenC2 response headers.
        :param encode: String specifying the serialization format for the response.

        :return: Serialized OpenC2 Response
        """
        message = OpenC2Msg(headers=OpenC2Headers(request_id=headers.request_id,
                                                  from_='yuuki', to=headers.from_,
                                                  created=round(time() * 1000)),
                            body=OpenC2Body(openc2=OpenC2Rsp(response=response_body)))
        response = message.dict(by_alias=True, exclude_unset=True)
        logging.info(f'Response:\n{pformat(response)}')
        return self.serializations[encode].serialize(response)

    def get_actuator_callable(self, oc2_msg: OpenC2Msg) -> Callable[[], OpenC2RspFields]:
        """Identifies the appropriate function to perform the received OpenC2 command

        :param oc2_msg: The OpenC2 message received by the consumer.

        :return: The function with the received OpenC2 command supplied as an argument.
        """

        oc2_cmd = oc2_msg.body.openc2.request

        if oc2_cmd.action == 'query' and oc2_cmd.target_name == 'features':
            function = self.query_features
        elif oc2_cmd.action in self.dispatch and oc2_cmd.target_name in self.dispatch[oc2_cmd.action]:
            if oc2_cmd.actuator_name is None:
                # Behavior of duplicate action-target pair functions (and their response(s))
                # is undefined in the OpenC2 language, so we don't try to solve that here,
                # and instead just call the first matching function
                function = next(iter(self.dispatch[oc2_cmd.action][oc2_cmd.target_name].values()))
            else:
                if oc2_cmd.actuator_name in self.dispatch[oc2_cmd.action][oc2_cmd.target_name]:
                    function = self.dispatch[oc2_cmd.action][oc2_cmd.target_name][oc2_cmd.actuator_name]
                else:
                    raise TypeError(f'No actuator: {oc2_cmd.actuator_name}')
        else:
            raise TypeError(f'No action-target pair for {oc2_cmd.action} {oc2_cmd.target_name}')

        logging.debug(f'Will call a function named: {function.__name__}')
        return partial(function, oc2_cmd)

    def query_features(self, oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
        """Implementation of the 'query features' command as described in the OpenC2 Language Specification
        https://docs.oasis-open.org/openc2/oc2ls/v1.0/oc2ls-v1.0.html#41-implementation-of-query-features-command
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

    def add_actuator_profile(self, actuator: Actuator) -> None:
        """Adds the actuator's functions to the consumer and adds the actuator's nsid to the list of supported profiles

        :param actuator: The actuator whose functions will be added to the consumer.
        """
        if actuator.nsid not in self.profiles:
            self.profiles.append(actuator.nsid)
        self.pairs.update(actuator.pairs)
        self.dispatch.update(actuator.dispatch)

    def add_serialization(self, serialization: Serialization) -> None:
        """Adds the serialization to the Consumer, enabling it to serialize and deserialize messages using the
        serialization's methods.

        :param serialization: The serialization to be added to the consumer.
        """
        self.serializations[serialization.name] = serialization
