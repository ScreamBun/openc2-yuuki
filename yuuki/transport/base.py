import asyncio
import logging
import pprint
import time

from ..openc2.oc2_types import OC2Msg, OC2Headers, OC2Body, OC2Rsp, OC2RspParent, StatusCode


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

    def set_serialization(self, serialization):
        self.serialization = serialization

    def start(self):
        raise NotImplementedError

    async def get_response(self, raw_data):
        try:
            data_dict = self.serialization.deserialize(raw_data)
            logging.info('Received payload as a Python Dict:\n{}'.format(nice_format(data_dict)))
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                             status_text='Deserialization to Python Dict failed: {}'.format(e))
            return self.make_response_msg(oc2_body, None)

        if "headers" not in data_dict.keys() or "body" not in data_dict.keys():
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST, status_text='OpenC2 message missing headers and/or body.')
            return self.make_response_msg(oc2_body, None)

        try:
            oc2_msg_in = OC2Msg.init_from_dict(data_dict)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                             status_text='Conversion from Python Dict to Obj failed: {}'.format(e))
            return self.make_response_msg(oc2_body, None)

        try:
            actuator_callable = self.cmd_handler.get_actuator_callable(oc2_msg_in)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST, status_text='Message Dispatch failed: {}'.format(e))
            return self.make_response_msg(oc2_body, oc2_msg_in.headers.from_)

        loop = asyncio.get_running_loop()
        try:
            oc2_body = await loop.run_in_executor(None, actuator_callable)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST, status_text='Actuator failed: {}'.format(e))
            return self.make_response_msg(oc2_body, None)

        try:
            return self.make_response_msg(oc2_body, oc2_msg_in.headers.from_)
        except Exception as e:
            oc2_body = OC2Rsp(status=StatusCode.NOT_FOUND, status_text='Serialization failed: {}'.format(e))
            return self.make_response_msg(oc2_body, oc2_msg_in.headers.from_)

    def make_response_msg(self, oc2_body, to):
        oc2_rsp = OC2Msg(headers=OC2Headers(from_='yuuki', to=to, created=int(round(time.time() * 1000))),
                         body=OC2Body(openc2=OC2RspParent(oc2_body)))
        response = oc2_rsp.to_dict()
        logging.info('Sending Response :\n{}'.format(nice_format(response)))
        oc2_msg = self.serialization.serialize(response)
        return oc2_msg
