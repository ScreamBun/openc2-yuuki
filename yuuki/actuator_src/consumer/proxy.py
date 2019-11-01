import argparse
import textwrap
from   configparser import ConfigParser
from   flask import Flask, jsonify, abort, request

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources

from .dispatch import Dispatcher

app = Flask(__name__)
ACTUATORS = None

YUUKI_CONFIG_FILE = 'yuuki.conf'
NOT_FOUND = 'default not found'
BOLD  = '\033[1m'
RED   = '\033[31m'
GREEN = '\033[32m'
END   = '\033[0m'

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
    the_json = request.get_json()
    retval = ACTUATORS.dispatch(the_json)

    return retval.as_dict()


class Proxy():
    def __init__(self):
        """
        """
        _config   = self._read_yuuki_config_file()
        _defaults = _config.get('defaults', {})
        self.endpoint  = _defaults.get('endpoint', NOT_FOUND)

    def get_opts(self):
        """
        """
        
        desc = textwrap.dedent(f'''\
        {BOLD}Start a proxy server to receive then dispatch OpenC2 Commands{END}
            {GREEN}Defaults{END} are sourced from {BOLD}yuuki.conf{END}
            ''')
        self.parser = argparse.ArgumentParser(description=desc,
                                         usage='%(prog)s [--enpoint ENDPOINT]',
                                         add_help=False,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        
        self.common_group = self.parser.add_argument_group(f'{BOLD}OPTIONS{END}')

        COLOR = RED if self.endpoint == NOT_FOUND else GREEN
        self.common_group.add_argument('-e',
                                       '--endpoint',
                                       default=self.endpoint,
                                       help = f'Server Socket ({COLOR}{self.endpoint}{END})')        

        self.common_group.add_argument('-h',
                                       '--help',
                                       action='store_true')
        
        retval, fluff = self.parser.parse_known_args()

        return retval
    
    def _color_default(self, cmd_option):
        """
        """
        if cmd_option.default is None:
            return cmd_option
        
        if cmd_option.default == NOT_FOUND:
            color_start = RED
        else:
            color_start = GREEN
        color_end   = END

        opt = cmd_option

        help = f'({color_start}{opt.default}{color_end}) ' + opt.help
        return type(opt)(opt.short, opt.long, opt.nargs, opt.default, help)

    def _read_yuuki_config_file(self):
        """
        """

        config_file = resources.open_text('yuuki', YUUKI_CONFIG_FILE)

        config_reader = ConfigParser()
        config_reader.read_file(config_file)
        config_dict = {}

        for section_name in config_reader.sections():
            config_dict[section_name] = {}
            for name, value in config_reader.items(section_name):
                config_dict[section_name][name] = value

        return config_dict

    def run(self):
        """
        """
        opts = self.get_opts()
        if opts.help:
            self.parser.print_help()
            return

        global ACTUATORS
        ACTUATORS = Dispatcher()

        # Parse http://127.0.0.1:9001 .
        host_port = self.endpoint.split('/')[-1]
        print(self.endpoint)
        host, port = host_port.split(':')
        app.run(port=port, host=host)

