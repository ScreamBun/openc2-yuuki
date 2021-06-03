from yuuki.transport.opendxl_transport import OpenDxl
from yuuki.transport.opendxl_transport import OpenDXLConfig
from command_handler import CommandHandler

consumer = OpenDxl(CommandHandler(), OpenDXLConfig())
consumer.start()
