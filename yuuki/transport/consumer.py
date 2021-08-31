import logging
from time import time
from pprint import pformat
from concurrent.futures import ThreadPoolExecutor

from pydantic import ValidationError

from ..openc2.oc2_types import OC2Msg, OC2Headers, OC2Body, OC2Rsp, OC2RspFields, StatusCode
from ..serialization import deserialize, serialize


class Consumer:
    """Base class for any transports implemented."""

    def __init__(self, cmd_handler, transport_config):
        self.cmd_handler = cmd_handler
        self.transport_config = transport_config
        self.executor = ThreadPoolExecutor()

    def start(self):
        raise NotImplementedError

    def get_response(self, raw_data, encode):
        try:
            data_dict = deserialize(raw_data, encode)
        except KeyError:
            return self.make_response_msg(OC2RspFields(status=StatusCode.BAD_REQUEST,
                                                       status_text='Invalid serialization protocol'),
                                          encode='json')
        except (ValueError, TypeError) as e:
            return self.make_response_msg(OC2RspFields(status=StatusCode.BAD_REQUEST,
                                                       status_text=f'Deserialization to Python Dict failed: {e}'),
                                          encode=encode)

        if not isinstance(data_dict, dict):
            return self.make_response_msg(OC2RspFields(status=StatusCode.BAD_REQUEST,
                                                       status_text='Deserialization to Python Dict failed'),
                                          encode=encode)

        logging.info(f'Received payload as a Python Dict:\n{pformat(data_dict)}')

        if "headers" not in data_dict.keys() or "body" not in data_dict.keys():
            return self.make_response_msg(OC2RspFields(status=StatusCode.BAD_REQUEST,
                                                       status_text='OpenC2 message missing headers and/or body.'),
                                          encode=encode)

        try:
            oc2_msg_in = OC2Msg(**data_dict)
        except ValidationError as e:
            return self.make_response_msg(OC2RspFields(status=StatusCode.BAD_REQUEST,
                                                       status_text='Malformed OpenC2 message'),
                                          encode=encode)

        try:
            actuator_callable = self.cmd_handler.get_actuator_callable(oc2_msg_in)
        except NotImplementedError as e:
            return self.make_response_msg(OC2RspFields(status=StatusCode.BAD_REQUEST,
                                                       status_text='No matching actuator found'),
                                          headers=oc2_msg_in.headers,
                                          encode=encode)

        if oc2_msg_in.body.openc2.request.args and oc2_msg_in.body.openc2.request.args.response_requested:
            response_requested = oc2_msg_in.body.openc2.request.args.response_requested
            if response_requested == 'none':
                self.executor.submit(actuator_callable)
                return None
            elif response_requested == 'ack':
                self.executor.submit(actuator_callable)
                return self.make_response_msg(OC2RspFields(status=StatusCode.PROCESSING), oc2_msg_in.headers, encode)
            elif response_requested == 'status':
                pass
            elif response_requested == 'complete':
                pass

        try:
            oc2_body = actuator_callable()
        except Exception as e:
            return self.make_response_msg(OC2RspFields(status=StatusCode.BAD_REQUEST,
                                                       status_text=f'Actuator failed: {e}'),
                                          encode=encode)

        try:
            return self.make_response_msg(oc2_body, oc2_msg_in.headers, encode)
        except (ValueError, TypeError) as e:
            oc2_body = OC2RspFields(status=StatusCode.NOT_FOUND, status_text=f'Serialization failed: {e}')
            return self.make_response_msg(oc2_body, oc2_msg_in.headers, encode)

    @staticmethod
    def make_response_msg(oc2_body, headers=OC2Headers(), encode=None):
        oc2_rsp = OC2Msg(headers=OC2Headers(request_id=headers.request_id,
                                            from_='yuuki', to=headers.from_,
                                            created=round(time() * 1000)),
                         body=OC2Body(openc2=OC2Rsp(response=oc2_body)))
        response = oc2_rsp.dict(by_alias=True)
        logging.info(f'Sending Response :\n{pformat(response)}')
        oc2_msg = serialize(response, encode)
        return oc2_msg
