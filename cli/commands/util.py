from os.path import exists as file_exists
from subprocess import check_output, Popen, PIPE
from re import match
import glob
from json import loads
from typing import Union
from requests import post
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


def validate_file_path(path):
    if not file_exists(path):
        msg = f'File not found: "{path}"'
        logger.error(msg)
        raise Exception(msg)
    return True


def http_api_helper(env: dict, route: str, data: dict, method=post) -> Union[bool, str]:
    if "server_data" not in env or env["server"] not in env["server_data"]:
        raise Exception("Server.json invalid")
    result_ok = False
    result_text = None
    secret = env["server_data"][env["server"]]["secret"]
    url = env["server_data"][env["server"]]["url"]
    endpoint = urljoin(url, route)
    logger.info(f'Requesting {endpoint}')
    try:
        got = method(
            endpoint,
            headers={
                "authorization": secret,
                "content-type": "application/x-www-form-urlencoded",
            },
            data=data,
        )

        result_ok = got.status_code == 200
        result_text = got.text
    except Exception as err:
        logger.error(result_text)
        result_ok = False
        result_text = str(err)

    return result_ok, result_text


def get_rfcmp_info_command(env, *args, **kwargs):
    files = args[0]
    pattern = r"(Name|Version|Type)=(.*)"
    results = {}
    for file in files:
        results[file] = {}
        try:
            ps = Popen(('strings', file), stdout=PIPE)
            output = check_output(
                ('grep', '-E', '(Version|Name|Type)'), stdin=ps.stdout)
            ps.wait()
            raw_matches = output.decode("utf-8").split("\n")
            for raw_match in raw_matches:
                if raw_match:
                    got = match(pattern, raw_match)
                    name = got.groups(1)[0]
                    value = got.groups(1)[1]
                    results[file][name] = value
        except:
            logger.error("File read error")
            return False
    logger.info(results)
    return True


def get_components_in_directory_command(env, *args, **kwargs):
    base_folder = args[0][0]
    files = glob.glob(base_folder + '/**/*.rfcmp', recursive=True)
    components = []
    for file in files:
        component_in_file = get_rfcmp_info_command(env, [file], kwargs)
        components.append(component_in_file)
    logger.info(components)
    return True


def check_config_command(env, *args, **kwargs):
    config = args[0][0]
    with open(config, "r") as file:
        data = loads(file.read())
        logger.info(data)
