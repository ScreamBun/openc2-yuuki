import argparse

from yuuki import OpenDxlTransport, OpenDxlConfig

from consumer_example import consumer


parser = argparse.ArgumentParser(description="OpenDXL Consumer")
parser.add_argument("config_file", help="OpenDXL configuration file")
args = parser.parse_args()


consumer = OpenDxlTransport(consumer=consumer, config=OpenDxlConfig(config_file=args.config_file))
consumer.start()
