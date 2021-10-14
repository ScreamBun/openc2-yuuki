import logging
from time import time
from pprint import pformat
from concurrent.futures import ThreadPoolExecutor

from pydantic import ValidationError

from ..openc2.openc2_types import OpenC2Msg, OpenC2Headers, OpenC2Body, OpenC2Rsp, OpenC2RspFields, StatusCode
from ..serialization import deserialize, serialize


class Consumer:
    """Base class for any transports implemented."""

    def __init__(self, cmd_handler, transport_config):
        self.cmd_handler = cmd_handler
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

    def start(self):
        raise NotImplementedError

    def get_response(self, raw_data, encode):
        try:
            message = deserialize(raw_data, encode)
        except KeyError:
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Invalid serialization protocol')
            return self.make_response_msg(openc2_rsp, encode='json')
        except (ValueError, TypeError) as e:
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=f'Deserialization failed: {e}')
            return self.make_response_msg(openc2_rsp, encode=encode)

        logging.info(f'Received command:\n{pformat(message)}')

        try:
            openc2_cmd = OpenC2Msg(**message)
        except ValidationError:
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='Malformed OpenC2 message')
            return self.make_response_msg(openc2_rsp, encode=encode)

        try:
            actuator_callable = self.cmd_handler.get_actuator_callable(openc2_cmd)
        except NotImplementedError:
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text='No matching actuator found')
            return self.make_response_msg(openc2_rsp, headers=openc2_cmd.headers, encode=encode)

        if openc2_cmd.body.openc2.request.args and openc2_cmd.body.openc2.request.args.response_requested:
            response_requested = openc2_cmd.body.openc2.request.args.response_requested
            if response_requested == 'none':
                self.executor.submit(actuator_callable)
                return None
            elif response_requested == 'ack':
                self.executor.submit(actuator_callable)
                return self.make_response_msg(OpenC2RspFields(status=StatusCode.PROCESSING), openc2_cmd.headers, encode)
            elif response_requested == 'status':
                pass
            elif response_requested == 'complete':
                pass

        try:
            openc2_rsp = actuator_callable()
        except Exception as e:
            openc2_rsp = OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=f'Actuator failed: {e}')
            return self.make_response_msg(openc2_rsp, encode=encode)

        try:
            return self.make_response_msg(openc2_rsp, openc2_cmd.headers, encode)
        except (ValueError, TypeError) as e:
            openc2_rsp = OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text=f'Serialization failed: {e}')
            return self.make_response_msg(openc2_rsp, openc2_cmd.headers, encode)

    @staticmethod
    def make_response_msg(oc2_body, headers=OpenC2Headers(), encode=None):
        message = OpenC2Msg(headers=OpenC2Headers(request_id=headers.request_id,
                                                  from_='yuuki', to=headers.from_,
                                                  created=round(time() * 1000)),
                            body=OpenC2Body(openc2=OpenC2Rsp(response=oc2_body)))
        response = message.dict(by_alias=True)
        logging.info(f'Sending Response :\n{pformat(response)}')
        return serialize(response, encode)
