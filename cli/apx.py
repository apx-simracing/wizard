from os.path import isfile
from json import load
from os import path
from sys import argv
from args import parser
from router import SHELL_COMMANDS
import logging

SERVER_DATA = []
ROOT_PATH = path.dirname(path.realpath(__file__))
SERVERS_JSON_PATH = path.join(ROOT_PATH, "servers.json")

logging.basicConfig(filename=path.join(ROOT_PATH, "cli.log"), encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s')

def validate_servers_json(path=SERVERS_JSON_PATH):
    if not isfile(path):
        raise FileNotFoundError("Server config not existing")
    logging.debug(f"Servers file found: {path}")

def get_servers_data(path=SERVERS_JSON_PATH):
    with open(path, "r") as read_file:
        logging.debug(f"Reading file: {path}")
        return load(read_file)

def get_args():
    parsed_args = parser.parse_args()
    if parsed_args.cmd is None:
        logging.error("No cmd given")
        raise Exception("No cmd given")
    return parsed_args

# TODO: WIP, ask @Günther Hubspecht [HTTP 410] for usage requirements - args and config???
def run_command(server_hash, command, args=None, config=None):
    validate_servers_json()

    server_data = get_servers_data()
    env = {"server_data": server_data, "server": server_hash, "server_config": config}

    if command not in SHELL_COMMANDS:
        raise Exception(f"command {command} not found")

    cli_command = SHELL_COMMANDS[command]

    logging.info(f'Running command "{command}" env={env} args={args}')        
    
    result = cli_command(env, args)

    if not result:
        raise Exception(f"Command failed: {command} {args} result: {result}")


if __name__ == "__main__":
    
    validate_servers_json()
    
    server_data = get_servers_data()
    parsed_args = get_args()

    env_tpl = {"server_data": server_data, "server": None, "server_config": None}

    for server in parsed_args.server:
        config = parsed_args.config
        
        env = env_tpl.copy()
        env["server"] = server
        
        if config is not None:
            env["server_config"] = config
        
        if parsed_args.cmd not in SHELL_COMMANDS:
            raise Exception(f"command {parsed_args.cmd} not found")
        
        cli_command = SHELL_COMMANDS[parsed_args.cmd]

        logging.info(f'Running command "{parsed_args.cmd}" env={env} args={parsed_args.args}')        
        result = cli_command(env, parsed_args.args)
        
        if not result:
            raise Exception(f"Command failed: {parsed_args.cmd} {argv} result: {result}")
