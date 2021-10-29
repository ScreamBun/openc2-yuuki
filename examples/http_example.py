"""
Example Implementation of an OpenC2 Consumer with HTTP.

First a Command Handler is defined, then we instantiate
a Consumer with it and our chosen Transport (HTTP).
"""
from yuuki import Http, HttpConfig
from command_handler import cmdhandler


consumer = Http(cmdhandler, HttpConfig())
consumer.start()
