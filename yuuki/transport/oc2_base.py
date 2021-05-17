import asyncio
import logging
import pprint
import time

from ..openc2.oc2_types import OC2Msg, OC2Headers, OC2Body, OC2Rsp, OC2RspParent, StatusCode
from ..serialization import deserialize, serialize, serializations


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

    async def get_response(self, raw_data, serial, **kwargs):
        if isinstance(serial, tuple):
            decode, encode = serial
        else:
            decode = serial
            encode = serial

        try:
            if encode and decode in serializations:
                data_dict = deserialize(raw_data, decode)
            else:
                oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                                  status_text='Unsupported serialization protocol')
                return self.make_response_msg(oc2_body, OC2Headers(), 'json')
        except (ValueError, MemoryError) as e:
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text='Malformed request data')
            logging.exception(f'Deserialization to Python Dict failed: {e}')
            return self.make_response_msg(oc2_body, OC2Headers(), encode)

        if not isinstance(data_dict, dict):
            oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                              status_text='Deserialization to Python Dict failed')
            return self.make_response_msg(oc2_body, OC2Headers(), encode)

        logging.info(f'Received payload as a Python Dict:\n{nice_format(data_dict)}')

        if 'headers' not in data_dict or 'body' not in data_dict:
            if 'http' in kwargs:
                data_dict = dict(body=dict(openc2=dict(request=data_dict)))
                data_dict['headers'] = {}
                data_dict['headers']['request_id'] = kwargs['request_id'] if 'request_id' in kwargs else None
                data_dict['headers']['created'] = kwargs['date'] if 'date' in kwargs else None
                data_dict['headers']['from_'] = kwargs['from_'] if 'from_' in kwargs else None
            else:
                oc2_body = OC2Rsp(status=StatusCode.BAD_REQUEST,
                                  status_text='OpenC2 message missing headers and/or body.')
                return self.make_response_msg(oc2_body, OC2Headers(), encode)

        try:
            oc2_msg_in = OC2Msg.init_from_dict(data_dict)
        except Exception as e:
            logging.exception(f'Conversion from Python Dict to Obj failed: {e}')
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
                                            created=round(time.time() * 1000)),
                         body=OC2Body(openc2=OC2RspParent(oc2_body)))
        response = oc2_rsp.to_dict()
        logging.info(f'Sending Response :\n{nice_format(response)}')
        oc2_msg = serialize(response, encode)
        return oc2_msg
