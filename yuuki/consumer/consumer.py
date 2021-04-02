

class Consumer:
    """Main Yuuki class to run your consumer.

    Supply a cmd_handler, transport, and serialization,
    then start!

    """
    def __init__(self, *, cmd_handler=None, transport=None, serialization=None):
        self.cmd_handler = cmd_handler
        self.transport = transport
        self.serialization = serialization

    def start(self):
        self.transport.set_cmd_handler(self.cmd_handler)
        self.transport.set_serialization(self.serialization)
        

        self.transport.start()