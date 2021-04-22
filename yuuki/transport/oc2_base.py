import asyncio
import logging
import pprint
import time

from ..openc2.oc2_types import OC2Msg, OC2Headers, OC2Body, OC2Rsp, OC2RspParent, StatusCode
from ..serialization import deserialize, serialize


def nice_format(output):
    pp = pprint.PrettyPrinter()
    return pp.pformat(output)


class Transport:
    """Base class for any transports implemented."""

    def __init__(self, transport_config):
        self.config = transport_config
        self.process_config()

    def process_config(self):
        raise NotImplementedError

    def set_cmd_handler(self, cmd_handler):
        self.cmd_handler = cmd_handler

    def start(self):
        raise NotImplementedError

    async def get_response(self, raw_data, encode):
        try:
            data_dict = deserialize(raw_data, encode)
        except KeyError:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text='Invalid serialization protocol')
            return self.make_response_msg(oc2_body, OC2Headers(), 'json')
        except ValueError as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text=f'Deserialization to Python Dict failed: {e}')
            return self.make_response_msg(oc2_body, OC2Headers(), encode)

        if not isinstance(data_dict, dict):
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text='Deserialization to Python Dict failed')
            return self.make_response_msg(oc2_body, OC2Headers(), encode)

        logging.info(f'Received payload as a Python Dict:\n{nice_format(data_dict)}')

        if "headers" not in data_dict.keys() or "body" not in data_dict.keys():
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text='OpenC2 message missing headers and/or body.')
            return self.make_response_msg(oc2_body, OC2Headers(), encode)

        try:
            oc2_msg_in = OC2Msg.init_from_dict(data_dict)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text=f'Conversion from Python Dict to Obj failed: {e}')
            return self.make_response_msg(oc2_body, OC2Headers(), encode)

        try:
            actuator_callable = self.cmd_handler.get_actuator_callable(oc2_msg_in)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text=f'Message Dispatch failed: {e}')
            return self.make_response_msg(oc2_body, oc2_msg_in.headers, encode)

        loop = asyncio.get_running_loop()
        try:
            oc2_body = await loop.run_in_executor(None, actuator_callable)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text=f'Actuator failed: {e}')
            return self.make_response_msg(oc2_body, OC2Headers(), encode)

        try:
            return self.make_response_msg(oc2_body, oc2_msg_in.headers, encode)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.NOT_FOUND,
                              status_text=f'Serialization failed: {e}')
            return self.make_response_msg(oc2_body, oc2_msg_in.headers, encode)

    @staticmethod
    def make_response_msg(oc2_body, headers, encode):
        oc2_rsp = OC2Msg(headers=OC2Headers(request_id=headers.request_id,
                                            from_='yuuki', to=headers.from_,
                                            created=int(round(time.time() * 1000))),
                         body=OC2Body(openc2=OC2RspParent(oc2_body)))
        response = oc2_rsp.to_dict()
        logging.info(f'Sending Response :\n{nice_format(response)}')
        oc2_msg = serialize(response, encode)
        return oc2_msg
