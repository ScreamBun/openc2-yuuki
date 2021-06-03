"""
Example Implementation of an OpenC2 Consumer with HTTP and JSON.

First a Command Handler is defined, then we instantiate
a Consumer with it and our chosen Transport(HTTP) and Serialization(Json).

To keep the file short and sweet, we use wildcard * imports and no comments.
See the mqtt_example.py for details.
"""

from yuuki import Http, HttpConfig
from command_handler import CommandHandler


consumer = Http(CommandHandler(), HttpConfig())
consumer.start()
