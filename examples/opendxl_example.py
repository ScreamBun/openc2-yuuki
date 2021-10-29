from yuuki import OpenDxl, OpenDXLConfig
from command_handler import cmdhandler

consumer = OpenDxl(cmdhandler, OpenDXLConfig())
consumer.start()
