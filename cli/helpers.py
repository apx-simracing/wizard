import logging
from os import path
from os.path import isfile
from json import load

if __package__ is None or __package__ == '':
    from commands.router import SHELL_COMMANDS
else:
    from cli.commands.router import SHELL_COMMANDS


logger = logging.getLogger(__name__)

ROOT_PATH = path.dirname(path.realpath(__file__))
SERVERS_JSON_PATH = path.join(ROOT_PATH, "servers.json")

def get_servers_data(path=SERVERS_JSON_PATH):
    if not isfile(path):
        logging.error(f"Servers file not found: {path}")
        raise FileNotFoundError("Server config not existing")
    with open(path, "r") as read_file:
        logging.debug(f"Reading file: {path}")
        return load(read_file)

# TODO: WIP, ask @Günther Hubspecht [HTTP 410] for usage requirements - args and config???
def run_apx_package_command(server_hash=None, command=None, args=None):

    if args is not None:
        
        if not isinstance(args, list) or len(args) == 0:
            msg = f'APX package command args need to be not emty list, got args={args}'
            logging.error(msg)
            raise Exception(msg)
        
        # all cli commands expect args to be list of lists
        # args = [args,]

    server_data = get_servers_data()
    
    env = {"server_data": server_data, "server": server_hash, "server_config": None}

    if command not in SHELL_COMMANDS:
        msg = f'APX package command not found {command}'
        logger.error(msg)
        raise Exception(msg)

    cli_command = SHELL_COMMANDS[command]

    logger.info(f'APX package command running {command} server={server_hash} env={env} args={args}')        
    
    result = cli_command(env, args)

    if not result:
        msg = f"APX package command failed {command} server={server_hash} env={env} args={args} result={result}"
        logger.error(msg)
        raise Exception(msg)