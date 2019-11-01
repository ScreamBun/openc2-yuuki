import argparse
from   collections import namedtuple
from   configparser import ConfigParser
import json
import pprint
import textwrap
import requests
try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources
from . import data

YUUKI_CONFIG_FILE = 'yuuki.conf'
EXAMPLE_CMDS_FILE = 'example_commands.json'

NOT_FOUND = 'default not found'
BOLD  = '\033[1m'
RED   = '\033[31m'
GREEN = '\033[32m'
BLUE  = '\033[34m'
END   = '\033[0m'

class CmdSender():
    """
    """
    def __init__(self):
        """
        """
        self.example_cmds = self._read_example_commands_file()
        _config   = self._read_yuuki_config_file()
        _defaults = _config.get('defaults')

        endpoint  = _defaults.get('endpoint', NOT_FOUND)

        Cmd       = namedtuple('Cmd', 'name function help cmd_options')
        CmdOption = namedtuple('CmdOption', 'short long positional nargs default help ')

        opt_endpoint  = self._color_default(CmdOption('e', 'endpoint',     False, None, endpoint,  'Remote socket'             ))
        opt_help      = self._color_default(CmdOption('h', 'help',         False, None, None,      'Show help and exit'        ))
        opt_cmd_index = self._color_default(CmdOption('c', 'command_index',True, '*'  , None,      'Which command in example_commands.json'))

        cmds = []
        cmds.append(Cmd('type-it', self.cmd_send_from_cli,  'Manually type and send a command',                      ()              ))
        cmds.append(Cmd('send',    self.cmd_send_from_file, 'Send a cmd from example_commands.json, based on index', (opt_cmd_index,)))
        cmds.append(Cmd('show',    self.cmd_show,           'Display the cmds found in example_commands.json file',  (opt_cmd_index,)))
        
        # This is everything we care about:
        self.cmds = cmds
        self.common_options = (opt_endpoint, opt_help)

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
    
    def _read_example_commands_file(self):
        """
        """
        stream = resources.open_text('yuuki.client_src.data', EXAMPLE_CMDS_FILE)
        return json.load(stream)
    
    def _add_opts(self, opts, parent):
        """
        """
        for opt in opts:
            if opt.positional:
                parent.add_argument(opt.long, help=opt.help, nargs=opt.nargs)
            elif opt.default is None:
                parent.add_argument('-'     + opt.short,
                                    '--'    + opt.long,
                                    help    = opt.help,
                                    action  = 'store_true')
            else:
                parent.add_argument('-'     + opt.short,
                                    '--'    + opt.long,
                                    help    = opt.help,
                                    default = opt.default)
    def _get_opts(self):
        desc = textwrap.dedent(f'''\
        {BOLD}Send OpenC2 commands to a local consumer ENDPOINT{END}
            {GREEN}Defaults{END} are sourced from {BOLD}yuuki.conf{END}
        
        {BOLD}EXAMPLES:{END}
            Manually type and send an OpenC2 command:
        
                > ./command_sender.py type-it
                > {{
                > "action" : "deny",
                > "target" : {{"domain_name" : "evil.com"}}
                > }}
            
            Send OpenC2 command #2 from the examples file:

                > ./command_sender.py send 2

            Show OpenC2 command #2 from the examples file:

                > ./command_sender.py show 2
            
            ''')
        self.parser = argparse.ArgumentParser(description=desc,
                                         usage='%(prog)s [options] <command> [sub-options]',
                                         add_help=False,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        
        common_group = self.parser.add_argument_group(f'{BOLD}OPTIONS{END}')
        self._add_opts(self.common_options, common_group)

        subparsers = self.parser.add_subparsers(title=f'{BOLD}COMMANDS{END}',
                                                dest='cmd',
                                                metavar='')
        for cmd in self.cmds:
            sub = subparsers.add_parser(cmd.name,
                                        help   = cmd.help,
                                        usage = '{0} [{0}-options]'.format(cmd.name))
            sub.set_defaults(func=cmd.function)
            self._add_opts(cmd.cmd_options, sub)
        
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
        return type(opt)(opt.short, opt.long, opt.positional, opt.nargs, opt.default, help)
    
    def _color_cmd(self, input ):
        """
        """
        replace_me = ["'action':", "'target':", "'args':","'actuator':"]
        colors     = [GREEN, GREEN, GREEN, GREEN]
        colorer = lambda x, color : f"{color}{x}{END}"
        for item, color in zip(replace_me, colors):
            input = input.replace(item, colorer(item, color))
        return input
    
    def _color_response(self, input ):
        """
        """
        replace_me = ["'status':", "'status_text':", "'results':",]
        colors     = [BLUE, BLUE, BLUE ]
        colorer = lambda x, color : f"{color}{x}{END}"
        for item, color in zip(replace_me, colors):
            input = input.replace(item, colorer(item, color))
        return input

    def _send(self, opts, cmd):
        """
        """
        print()
        print('>>> COMMAND')

        visible_cmd = pprint.pformat(cmd)
        print(self._color_cmd(visible_cmd))
        print()

        headers  =  {"Content-Type": "application/json"}
        response = requests.post(opts.endpoint, json=cmd, headers=headers)

        print('<<< RESPONSE')
        thing = pprint.pformat(response.json())
        print(self._color_response(thing))
        print()

    def cmd_send_from_file(self, opts):
        """
        """
        cmd = self.example_cmds[int(opts.command_index[0])]['cmd']
        self._send(opts, cmd)

    def cmd_send_from_cli(self, opts):
        """
        """
        instructions = textwrap.dedent(f'''\

            {BOLD}Enter a [multi-line] JSON-formatted OpenC2 command.{END}
            (hit Enter when done, or Enter now to see an example.)''')
        
        example = textwrap.dedent(f'''\
            {BOLD}Example:{END}

            {{
            "action" : "deny",
            "target" : {{ "domain_name": "evil.com"}}
            }}
            ''')
        
        print(instructions)
        
        prompt = ''
        retval = ''

        try:
            for line in iter(lambda: input(prompt), ''):
                retval += line
        except KeyboardInterrupt:
            return None
        
        if len(retval) < 1:
            print(example)
            return None
        
        retval = retval.strip()
        
        if not retval.startswith('{'):
            retval = '{' + retval
        if not retval.endswith('}'):
            retval += '}'
        
        try:
            retval = json.loads(retval)
        except json.decoder.JSONDecodeError as e:
            print(f'Could not parse JSON: {e}')
            return None        

        self._send(opts, retval)

    def cmd_show(self, opts):
        """
        """
        if opts.command_index:
            # User has specified command(s) to show
            try:
                for command_index in opts.command_index:
                    thing = self.example_cmds[int(command_index)]['cmd']
                    print(command_index, thing)
            except IndexError:
                pass
        else:
            # User wants to see all commands.
            for i in range(len(self.example_cmds)):
                cmd = self.example_cmds[i]['cmd']
                print(i, cmd)
    
    def run(self):
        """
        """
        opts = self._get_opts()

        # Check for basic sanity
        if not opts.cmd and opts.help:
            self.parser.print_help()
        elif not opts.cmd:
            self.parser.print_usage()
        else:
            opts.func(opts)


