import asyncio
import logging
import pprint
import time

from ..openc2.oc2_types import OC2Msg, OC2Rsp, OC2RspParent, StatusCode


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
            oc2_msg = self.make_response_msg(StatusCode.BAD_REQUEST,
                                             'Deserialization to Python Dict failed: {}'.format(e), None)
            return self.serialization.serialize(oc2_msg.to_dict())

        if "headers" not in data_dict.keys() or "body" not in data_dict.keys():
            oc2_msg = self.make_response_msg(StatusCode.BAD_REQUEST,
                                             'OpenC2 message missing headers and/or body.', None)
            return self.serialization.serialize(oc2_msg.to_dict())

        try:
            oc2_msg_in = OC2Msg.init_from_dict(data_dict)
        except Exception as e:
            oc2_msg = self.make_response_msg(StatusCode.BAD_REQUEST,
                                             'Conversion from Python Dict to Obj failed: {}'.format(e), None)
            return self.serialization.serialize(oc2_msg.to_dict())

        try:
            actuator_callable = self.cmd_handler.get_actuator_callable(oc2_msg_in)
        except Exception as e:
            oc2_msg = self.make_response_msg(StatusCode.BAD_REQUEST, 'Message Dispatch failed: {}'.format(e),
                                             oc2_msg_in.headers.from_)
            return self.serialization.serialize(oc2_msg.to_dict())

        loop = asyncio.get_running_loop()

        try:
            oc2_rsp = await loop.run_in_executor(None, actuator_callable)
        except Exception as e:
            oc2_msg = self.make_response_msg(StatusCode.BAD_REQUEST, 'Actuator failed: {}'.format(e),
                                             oc2_msg_in.headers.from_)
            return self.serialization.serialize(oc2_msg.to_dict())

        try:
            oc2_msg_out = self.make_response_msg(None, None, oc2_msg_in.headers.from_)
            oc2_msg_out.body.openc2 = oc2_rsp
            logging.info('Sending Response :\n{}'.format(nice_format(oc2_msg_out.to_dict())))
            serialized = self.serialization.serialize(oc2_msg_out.to_dict())
            return serialized
        except Exception as e:
            oc2_msg = self.make_response_msg(StatusCode.BAD_REQUEST, 'Serialization failed: {}'.format(e),
                                             oc2_msg_in.headers.from_)
            return self.serialization.serialize(oc2_msg.to_dict())

    @staticmethod
    def make_response_msg(status, status_text, to):
        oc2_msg = OC2Msg()
        oc2_msg.body.openc2 = OC2RspParent()
        oc2_msg.headers.created = int(round(time.time() * 1000))
        oc2_msg.body.openc2.response.status = status
        oc2_msg.body.openc2.response.status_text = status_text
        oc2_msg.headers.from_ = 'yuuki'
        oc2_msg.headers.to = to
        return oc2_msg
