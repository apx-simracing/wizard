import logging
from os import path
from sys import argv


if __package__ is None or __package__ == '':
    from args import parser
    from helpers import get_servers_data
    from commands.router import SHELL_COMMANDS
else:
    from cli.args import parser
    from cli.helpers import get_servers_data
    from cli.commands.router import SHELL_COMMANDS


ROOT_PATH = path.dirname(path.realpath(__file__))

logging.basicConfig(filename=path.join(ROOT_PATH, "cli.log"),
                    encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s')


def get_args():
    parsed_args = parser.parse_args()
    if parsed_args.cmd is None:
        logging.error("No cmd given")
        raise Exception("No cmd given")
    return parsed_args


if __name__ == "__main__":

    server_data = get_servers_data()
    parsed_args = get_args()

    env_tpl = {"server_data": server_data,
               "server": None, "server_config": None}

    for server in parsed_args.server:
        config = parsed_args.config

        env = env_tpl.copy()
        env["server"] = server

        if config is not None:
            env["server_config"] = config

        if parsed_args.cmd not in SHELL_COMMANDS:
            raise Exception(f"command {parsed_args.cmd} not found")

        cli_command = SHELL_COMMANDS[parsed_args.cmd]

        logging.info(
            f'Running command "{parsed_args.cmd}" env={env} args={parsed_args.args}')
        result = cli_command(env, parsed_args.args)

        if not result:
            raise Exception(
                f"Command failed: {parsed_args.cmd} {argv} result: {result}")
