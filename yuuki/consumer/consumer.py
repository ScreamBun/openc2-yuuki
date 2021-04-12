class Consumer:
    """
    Main Yuuki class to run your consumer.

    Supply a cmd_handler, transport, and serialization,
    then start!
    """

    def __init__(self, *, cmd_handler=None, transport=None):
        self.cmd_handler = cmd_handler
        self.transport = transport

    def start(self):
        self.transport.set_cmd_handler(self.cmd_handler)
        self.transport.start()
