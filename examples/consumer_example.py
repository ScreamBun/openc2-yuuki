"""
OpenC2 Consumer Example
"""

from yuuki import Consumer
from actuators.slpf import slpf


consumer = Consumer(rate_limit=60, versions=['1.0'], actuators=[slpf])
