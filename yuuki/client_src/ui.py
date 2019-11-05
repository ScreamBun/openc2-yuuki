import argparse
import json
import re
import textwrap
from ..config import Config
from . import data
from . import network


class UI():

    def __init__(self):
        c = Config.Console

        self.parser = argparse.ArgumentParser(
            usage="%(prog)s [options] <command> [sub-options]",
            add_help=False,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        self.parser.description = textwrap.dedent(f"""
            {c.BOLD}Send OpenC2 commands to a local consumer ENDPOINT{c.END}
                {c.DEFAULT}Defaults{c.END} are sourced from {c.BOLD}yuuki.conf{c.END}

            {c.BOLD}EXAMPLES:{c.END}
                Manually type and send an OpenC2 command:
                    > {self.parser.prog} type-it
                    > {{
                    > "action" : "deny",
                    > "target" : {{"domain_name" : "evil.com"}}
                    > }}

                Send OpenC2 command #2 from the examples file:
                    > {self.parser.prog} send 2

                Show OpenC2 command #2 from the examples file:
                    > {self.parser.prog} show 2
            """)

        # Common Args
        common_group = self.parser.add_argument_group(f"{c.BOLD}OPTIONS{c.END}")
        endpoint_help = f"({c.DEFAULT}{Config.defaults.endpoint}{c.END}) Remote socket"
        common_group.add_argument("-e", "--endpoint", default=Config.defaults.endpoint, help=endpoint_help)
        common_group.add_argument("-h", "--help", default=False, action="store_true", help="Show help and exit")

        # Sub Commands
        subparsers = self.parser.add_subparsers(
            title=f"{c.BOLD}COMMANDS{c.END}",
            dest="cmd",
            metavar=""
        )

        # Type-It command
        type_it_cmd = subparsers.add_parser(
            "type-it",
            help="Manually type and send a command",
            usage="type-it [type-it-options]"
        )
        type_it_cmd.set_defaults(func=self.cmd_send_from_cli)

        # Send command
        send_cmd = subparsers.add_parser(
            "send",
            help="Send a cmd from example_commands.json, based on index",
            usage="send [send-options]"
        )
        send_cmd.set_defaults(func=self.cmd_send_from_file)
        send_cmd.add_argument("command_index", nargs="*", help="Which command in example_openc2_commands.json")

        # Show command
        show_cmd = subparsers.add_parser(
            "show",
            help="Display the cmds found in example_commands.json file",
            usage="show [show-options]"
        )
        show_cmd.set_defaults(func=self.cmd_show)
        show_cmd.add_argument("command_index", nargs="*", help="Which command in example_openc2_commands.json")


    def parse_args(self, args: list = None) -> argparse.Namespace:
        if args:
            return self.parser.parse_args(args=args or ["--help"])
        
        options, args = self.parser.parse_known_args()
        return options    

    def _color_cmd(self, input):
        tags = ['action', 'target', 'args', 'actuator', 'command_id']
        return self._color_tags(input, tags, Config.Console.COMMAND)
    
    def _color_response(self, input):
        tags = ['status', 'status_text', 'results']
        return self._color_tags(input, tags, Config.Console.RESPONSE)

    def _color_tags(self, input, tags, color):
        for item in tags:
            pattern = f'(?<="){item}(?=":)'
            replace_with = f'{color}{item}{Config.Console.END}'
            input = re.sub(pattern, replace_with, input)
        return input

    def _send(self, endpoint: str, cmd: dict) -> None:
        c = Config.Console
        print()
        print(f'>>> {c.COMMAND}COMMAND{c.END}')

        visible_cmd = json.dumps(cmd, indent=3)
        print(self._color_cmd(visible_cmd))
        print()

        response = network.send(endpoint, cmd) # Shouldn't we send a json obj, not a dict?

        print(f'<<< {c.RESPONSE}RESPONSE{c.END}')
        visible_response = json.dumps(response.json(), indent=3)
        print(self._color_response(visible_response))
        print()

    def cmd_send_from_file(self, opts: argparse.Namespace) -> None:
        if not opts.command_index:
            print('Supply a command index, e.g. 0')
            return None
        try:
            cmd = data.get_cmd( int(opts.command_index[0]) )
        except IndexError as e:
            print(e)
            return None
        self._send(opts.endpoint, cmd)

    def cmd_send_from_cli(self, opts: argparse.Namespace) -> None:
        c = Config.Console
        
        print(textwrap.dedent(f"""
            {c.BOLD}Enter a [multi-line] JSON-formatted OpenC2 command.{c.END}
            (hit Enter when done, or Enter now to see an example.)
        """))

        prompt = ""
        cmd = ""

        try:
            for line in iter(lambda: input(prompt), ""):
                cmd += line
        except KeyboardInterrupt:
            return None
        
        if len(cmd) < 1:
            fmt_cmd = {"action": "deny", "target": {"domain_name": "evil.com"}}
            print(f"{c.BOLD}Example:{c.END}\n")
            print(json.dumps(fmt_cmd, indent=3))
            return None
        
        if not cmd.startswith('{'):
            cmd = '{' + cmd
        if not cmd.endswith('}'):
            cmd += '}'
        
        try:
            cmd = json.loads(cmd)
        except json.decoder.JSONDecodeError as e:
            print(f"Could not parse JSON: {e}")
            return None

        self._send(opts.endpoint, cmd)

    def cmd_show(self, opts: argparse.Namespace) -> None:
        cmds = data.get_all_cmds()
        
        def align_action_target(cmd):
            prefix, suffix = cmd.split(',', maxsplit=1)
            return '{0:<22}{1}'.format(prefix, suffix)

        if opts.command_index:
            # User has specified command(s) to show
            for idx in opts.command_index:
                try:
                    cmd = data.get_cmd(int(idx))
                except IndexError as e:
                    print(e)
                    continue
                
                print(idx, self._color_cmd(align_action_target(json.dumps(cmd))))
        else:
            # User wants to see all commands.
            for i, cmd in enumerate(data.get_all_cmds()):
                print(i, self._color_cmd(align_action_target(json.dumps(cmd))))
    
    def run(self) -> None:
        opts = self.parse_args()

        # Check for basic sanity
        if not opts.cmd and opts.help:
            self.parser.print_help()

        elif not opts.cmd:
            self.parser.print_usage()

        else:
            opts.func(opts)


def run():
    ui = UI()
    ui.run()