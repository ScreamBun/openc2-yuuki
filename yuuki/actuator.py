#!/usr/bin/env python3

from .actuator_src.consumer import proxy

if __name__ == '__main__':
    ui = proxy.Proxy()
    ui.run()