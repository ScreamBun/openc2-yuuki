#!/usr/bin/env python3

import requests
import sys
import json
import yaml
import re

HEADERS = {"Content-Type": "application/json"}

ACTUATOR = r"\A(\S+)\s+(\S+)\s+(\{.*\})\s+(\S+)\s+(\{.*\})(\s+.*)?\Z"
NO_ACTUATOR = r"\A(\S+)\s+(\S+)\s+(\{.*\})(\s+.*)?\Z"
TARGET_ONLY = r"\A(\S+)\s+(\S+)\Z"


def main():
    """
    OpenC2 debug shell
    """
    endpoint = None
    if len(sys.argv) == 2:
        endpoint = sys.argv[1]
        if endpoint.find("://") == -1:
            print("Warning: URI scheme not specified")

    print("OpenC2 debug shell (endpoint={})".format(endpoint))

    while True:
        try:
            cmd = parse(input("openc2> "))
            print(json.dumps(cmd, indent=4))
            
            if endpoint is not None:
                print("-->")
                print("<--")
                r = requests.post(endpoint, json=cmd, headers=HEADERS)
                print(json.dumps(r.json(), indent=4))

        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("^C")
        except Exception as e:
            print("{}: {}".format(e.__class__.__name__, str(e)))

    return 0


def parse(cmd):
    """
    Debug OpenC2 CLI parser
    """
    actuator_match = re.match(ACTUATOR, cmd)
    non_actuator_match = re.match(NO_ACTUATOR, cmd)
    target_only_match = re.match(TARGET_ONLY, cmd)

    action = None
    target_type = None
    target = {}
    actuator_type = None
    actuator = {}
    modifier = {}

    if actuator_match:
        groups = actuator_match.groups("")

        action = groups[0].lower()
        target_type = groups[1]
        target = yaml.safe_load(groups[2])

        actuator_type = groups[3]
        actuator = yaml.safe_load(groups[4])
        
        modifier = yaml.safe_load("{{{}}}".format(groups[5]))
    elif non_actuator_match:
        groups = non_actuator_match.groups("")

        action = groups[0].lower()
        target_type = groups[1]
        target = yaml.safe_load(groups[2])

        modifier = yaml.safe_load("{{{}}}".format(groups[3]))
    elif target_only_match:
        groups = target_only_match.groups("")

        action = groups[0].lower()
        target_type = groups[1]
    else:
        raise SyntaxError("Invalid OpenC2 command")


    target['type'] = target_type

    if actuator_match:
        actuator['type'] = actuator_type

    return {'action': action, 'target': target, 'actuator': actuator,
            'modifier': modifier}


if __name__ == "__main__":
    sys.exit(main())

