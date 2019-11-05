
from argparse import Namespace
from configparser import ConfigParser

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources


CONFIG_LOCATION = ('yuuki', 'yuuki.conf') # (Module_Name, File_Name)


def _parse_config(config_loc: tuple) -> dict:
    """
    """
    config_file = resources.open_text(*config_loc)

    parser = ConfigParser()
    parser.read_file(config_file)

    retval = {s: {k: v for k, v in parser.items(s)} for s in parser.sections()}

    return retval


class Config:
    """
    Config shared by both client and actuator, populated by yuuki.conf.
    """
    defaults = None

    class Console:
        """
        Console colors. No need to pollute yuuki.conf with these.
        """
        BOLD   = '\033[1m'
        _GREEN = '\033[32m'
        _BLUE  = '\033[34m'
        END    = '\033[0m'

        DEFAULT  = _GREEN
        COMMAND  = _GREEN
        RESPONSE = _BLUE


# Populate Config class above with data from config file.
for k, v in _parse_config(CONFIG_LOCATION).items():
    v = Namespace(**v) if isinstance(v, dict) else v
    setattr(Config, k, v)

# Turn off coloring if needed.
if getattr(Config.defaults, 'console_coloring', 'Off') != 'On':
    Config.Console.BOLD = ''
    Config.Console.END = ''
    Config.Console.DEFAULT = ''
    Config.Console.COMMAND = ''
    Config.Console.RESPONSE = ''