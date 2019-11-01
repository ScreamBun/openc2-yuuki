#!/usr/bin/env python3

from .client_src.command_sender import CmdSender

if __name__ == '__main__':
    ui = CmdSender()
    ui.run()