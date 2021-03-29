import asyncio
import logging
import pprint
import time

from ..openc2.oc2_types import OC2Msg, OC2Rsp, OC2RspParent, StatusCode


class Transport():
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
            pp = pprint.PrettyPrinter()
            nice = pp.pformat(data_dict)
            logging.info('Received payload as a Python Dict:\n{}'.format(nice))

        except Exception as e:
            retval = self.make_response_msg()
            retval.body.openc2.response.status = StatusCode.BAD_REQUEST
            retval.body.openc2.response.status_text = 'Deserialization to Python Dict failed: {}'.format(e)
            
            return self.serialization.serialize(retval.to_dict())
        
        try:
            oc2_msg_in = OC2Msg.init_from_dict(data_dict)

        except Exception as e:
            retval = self.make_response_msg()
            retval.body.openc2.response.status = StatusCode.BAD_REQUEST
            retval.body.openc2.response.status_text = 'Conversion from Python Dict to Obj failed: {}'.format(e)
            
            return self.serialization.serialize(retval.to_dict())

        try:
            actuator_callable = self.cmd_handler.get_actuator_callable(oc2_msg_in)
        except Exception as e:
            retval = self.make_response_msg()
            retval.body.openc2.response.status = StatusCode.BAD_REQUEST
            retval.body.openc2.response.status_text = 'Message Dispatch failed: {}'.format(e)
            
            return self.serialization.serialize(retval.to_dict())
        
        
        loop = asyncio.get_running_loop()
        try:
            oc2_rsp = await loop.run_in_executor(None, actuator_callable)

        except Exception as e:
            retval = self.make_response_msg()
            retval.body.openc2.response.status = StatusCode.BAD_REQUEST
            retval.body.openc2.response.status_text = 'Actuator failed: {}'.format(e)
            
            return self.serialization.serialize(retval.to_dict())


        try:
            oc2_msg_out = self.make_response_msg()
            oc2_msg_out.headers.from_ = 'yuuki'
            oc2_msg_out.headers.to = oc2_msg_in.headers.from_
            oc2_msg_out.body.openc2 = oc2_rsp
            pp = pprint.PrettyPrinter()
            nice = pp.pformat(oc2_msg_out.to_dict())
            logging.info('Sending Response :\n{}'.format(nice))
            serialized = self.serialization.serialize(oc2_msg_out.to_dict())
            return serialized
        except Exception as e:
            retval = self.make_response_msg()
            retval.body.openc2.response.status = StatusCode.BAD_REQUEST
            retval.body.openc2.response.status_text = 'Serialization failed: {}'.format(e)
            
            return self.serialization.serialize(retval.to_dict())

    @staticmethod
    def make_response_msg():
        retval = OC2Msg()
        retval.body.openc2 = OC2RspParent()
        retval.headers.created = int(round(time.time() * 1000))
        return retval