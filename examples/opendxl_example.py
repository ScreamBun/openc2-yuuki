from yuuki import OpenDxl, OpenDXLConfig
from slpf import slpf

consumer = OpenDxl(rate_limit=60, versions=['1.0'], opendxl_config=OpenDXLConfig(), actuators=[slpf])
consumer.start()
