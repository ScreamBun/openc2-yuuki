import json

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources



def _read_example_commands_file() -> list:
    """
    """
    stream = resources.open_text('yuuki.client_src.data', 'example_openc2_commands.json')
    return json.load(stream)


def get_cmd(cmd_index : int) -> list:
    try:
        return _example_cmds[cmd_index].copy()
    except IndexError:
        raise IndexError('Valid indicies are 0-{}'.format(len(_example_cmds) -1))

def get_all_cmds() -> list:
    return _example_cmds.copy()


_example_cmds = _read_example_commands_file()