#!/usr/bin/env python3

import requests
import sys
import json
import yaml
import re

HEADERS = {"Content-Type": "application/json"}

_BASE_REGEX = r"\A(?P<action>\S+)\s+(?P<target_type>\S+)"
ACTUATOR    = _BASE_REGEX + r"\s+(?P<target>\{.*\})\s+(?P<actuator_type>\S+)\s+(?P<actuator>\{.*\})(?P<modifier>\s+.*)?\Z"
NO_ACTUATOR = _BASE_REGEX + r"\s+(?P<target>\{.*\})(?P<modifier>\s+.*)?\Z"
TARGET_ONLY = _BASE_REGEX + r"\Z"

def main():
    """
    Run the OpenC2 debug shell.
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
    Format the user's input into a nested dictionary.
    """
    actuator_match     = re.match(ACTUATOR,    cmd)
    non_actuator_match = re.match(NO_ACTUATOR, cmd)
    target_only_match  = re.match(TARGET_ONLY, cmd)

    action = None
    target_type = None
    target = {}
    actuator_type = None
    actuator = {}
    modifier = {}

    if actuator_match:
        groups = actuator_match.groupdict()

        action      = groups['action'].lower()
        target_type = groups['target_type']
        target      = yaml.safe_load(groups['target'])

        actuator_type = groups['actuator_type']
        actuator      = yaml.safe_load(groups['actuator'])
        
        modifier = yaml.safe_load("{{{}}}".format(groups['modifier']))
    elif non_actuator_match:
        groups = non_actuator_match.groupdict()

        action      = groups['action'].lower()
        target_type = groups['target_type']
        target      = yaml.safe_load(groups['target'])

        modifier = yaml.safe_load("{{{}}}".format(groups['modifier']))
    elif target_only_match:
        groups = target_only_match.groupdict()

        action      = groups['action'].lower()
        target_type = groups['target_type']
    else:
        raise SyntaxError("Invalid OpenC2 command")

    target['type'] = target_type

    if actuator_match:
        actuator['type'] = actuator_type

    retval = {'action': action, 'target': target, 'actuator': actuator,
            'modifier': modifier}
    return retval


if __name__ == "__main__":
    sys.exit(main())

