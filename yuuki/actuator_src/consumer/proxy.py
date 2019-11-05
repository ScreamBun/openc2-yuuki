from flask import (
    Flask,
    jsonify,
    abort,
    request
)
import json
from .dispatch import Dispatcher


app = Flask(__name__)
app.dispatcher = None


@app.errorhandler(400)
def bad_request(e):
    """
    Respond to a malformed OpenC2 command.
    """
    return jsonify({"response": "400 Bad Request"}), 400


@app.errorhandler(500)
def internal_server_error(e):
    """
    Uncaught proxy error.
    """
    return jsonify({"response": "500 Internal Server Error"}), 500


@app.route('/')
def ok():
    """
    Verify the system is running.
    """
    return jsonify({"response": "200 OK"}), 200


@app.route('/', methods=['POST'])
def recieve():
    """
    Recieve an OpenC2 command, process and return response.

    All OpenC2 commands should be application/json over HTTP POST.
    """
    if not request.json:
        abort(400)
    data = request.get_json()
    oc2_response = app.dispatcher.dispatch(data)
    retval = json.dumps(oc2_response.as_dict())

    return retval


def run(host, port):
    """
    """
    app.dispatcher = Dispatcher()
    app.run(port=port, host=host)

