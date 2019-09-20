#!/usr/bin/env python3

import argparse
import os
from flask import Flask, jsonify, request, abort
from .dispatch import Dispatcher
from configparser import SafeConfigParser

app = Flask(__name__)

PROFILE = None

@app.route('/')
def ok():
    """
    Verify the system is running.
    """
    return jsonify({"response": "200 OK"}), 200


@app.errorhandler(400)
def bad_request(e):
    """
    Respond to a malformed OpenC2 command.
    """
    return jsonify({"response": "400 Bad Request"}), 400


@app.errorhandler(500)
def internal_server_error(e):
    """
    Uncaught proxy error
    """
    return jsonify({"response": "500 Internal Server Error"}), 500


@app.route('/', methods=['POST'])
def recieve():
    """
    Recieve an OpenC2 command, process and return response.

    All OpenC2 commands should be application/json over HTTP POST
    """
    if not request.json:
        abort(400)

    response = PROFILE.dispatch(request.get_json())
    return jsonify(response), 200

def parse_config(config_file):

    """
    Receive a file path and parse it to a dict
    """

    config_reader = SafeConfigParser()
    config_reader.read(config_file)
    config_dict = {}

    for section_name in config_reader.sections():

        config_dict[section_name] = {}

        for name, value in config_reader.items(section_name):

            config_dict[section_name][name] = value
    
    return config_dict

def main():

    """
    Parse configuration and start flask app.
    -
    -    WARNING: Multiple profiles are currently subtly broken in dispatch.py; 
         spreading the logic for different actions across multiple .py files should work correctly,
         but spreading the logic for the same action across multiple files will not; 
         only the target/actuator types from the last profile will be run.
    """
    global PROFILE

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=None, help="port to listen on (default=9001)")    

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--conf', default=None)
    group.add_argument('--profiles', nargs='+', default=None)


    args = parser.parse_args()

    if args.profiles:

        # If a profile is specified by switches

        # Make dispatcher with loaded modules     
        PROFILE = Dispatcher(args.profiles)

        # Run the app    
        if args.port:

            app.run(port=int(args.port),host="127.0.0.1")

        else:

            app.run(port=9001,host="127.0.0.1")

    else:

        # If a config file is specified
        if os.path.isfile(args.conf):

            app.config["yuuki"] = parse_config(args.conf)

        else:

            raise(Exception("Config file not found")) 

        # Load profiles
        profile_list = []

        for profile in app.config["yuuki"]["profiles"]:
           
            print(' * Loading profile {}'.format(profile))

            profile_list.append(app.config["yuuki"]["profiles"][profile])
        
        # Make dispatcher with loaded modules    
        PROFILE = Dispatcher(profile_list)

        if args.port:

            # Run the app:   
            app.run(port=int(args.port),host=app.config["yuuki"]["server"]["host"])
        else:

        # Run the app:
            app.run(port=int(app.config["yuuki"]["server"]["port"]),host=app.config["yuuki"]["server"]["host"])

if __name__ == "__main__":

    main()

