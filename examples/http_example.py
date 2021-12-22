"""
Example Implementation of an OpenC2 HTTP Consumer
"""
from yuuki import Http, HttpConfig
from slpf import slpf

consumer = Http(rate_limit=60, versions=['1.0'], http_config=HttpConfig(), actuators=[slpf])
consumer.start()
