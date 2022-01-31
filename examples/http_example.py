"""
Example Implementation of an OpenC2 HTTP Consumer
"""
from yuuki import HttpTransport, HttpConfig
from consumer_example import consumer

http_consumer = HttpTransport(consumer=consumer, config=HttpConfig())
http_consumer.start()
