from requests import post, get
from os.path import basename
from json import loads, dumps
from .util import http_api_helper, validate_file_path
import logging

logger = logging.getLogger(__name__)

def deploy_command(env, *args, **kwargs) -> bool:
    server_key = env["server"]
    server_data = env["server_data"][server_key]
    url = server_data["url"]
    secret = server_data["secret"]

    is_running_command, running_text = http_api_helper(env, "status", {}, get)
    if not is_running_command:
        raise Exception("Status check failed")

    status_json = loads(running_text)
    if status_json and "not_running" not in status_json:
        raise Exception("Server is running, deploy failed")
    
    file_name = args[0][0]
    validate_file_path(file_name)
    
    rfm_filename = args[0][1]
    validate_file_path(rfm_filename)

    result = False
    upload_files = {}
    with open(file_name, "r") as file:
        data = file.read()
        # add grip, if possible
        json_data = loads(data)
        if "conditions" in json_data and json_data["conditions"] is not None:
            for session_key, gripfile in json_data["conditions"].items():
                if gripfile is not None:
                    upload_files[session_key] = open(gripfile, "rb").read()

        got = post(
            url + "/deploy",
            headers={"authorization": secret},
            data={"config": data, "rfm_config": open(rfm_filename, "r").read()},
            files=upload_files,
        )

        result = got.status_code == 200
    return result


def weather_update_command(env, *args, **kwargs) -> bool:
    server_key = env["server"]
    server_data = env["server_data"][server_key]
    url = server_data["url"]
    secret = server_data["secret"]

    is_running_command, running_text = http_api_helper(env, "status", {}, get)
    if not is_running_command:
        raise Exception("Status check failed")

    status_json = loads(running_text)
    if status_json and "not_running" not in status_json:
        raise Exception("Server is running, deploy failed")
    
    file_name = args[0][0]
    validate_file_path(file_name)

    result = False
    # upload_files = {}
    with open(file_name, "r") as file:
        data = file.read()
        # add grip, if possible
        # json_data = loads(data)

        # TODO: why not json_data?
        got = post(
            url + "/weather",
            headers={"authorization": secret},
            data={"config": data},
        )

        result = got.status_code == 200
    return result


def install_command(env, *args, **kwargs) -> bool:

    is_running_command, running_text = http_api_helper(env, "status", {}, get)
    if not is_running_command:
        raise Exception("Status check failed")

    status_json = loads(running_text)
    if "not_running" not in status_json:
        raise Exception("Server is running, install failed")
    
    got, text = http_api_helper(env, "install", {}, get)
    logger.info(text)
    return got


def unlock_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        server_key = env["server"]
        server_data = env["server_data"][server_key]
        url = server_data["url"]
        secret = server_data["secret"]
        file = args[0][0]
        validate_file_path(file)
        got = post(
            url + "/unlock",
            headers={"authorization": secret},
            files={"unlock": open(file, "rb")},
        )
        return True


def install_plugins_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        server_key = env["server"]
        server_data = env["server_data"][server_key]
        url = server_data["url"]
        secret = server_data["secret"]
        # file = args[0][0]
        files = {}
        paths = {}
        for index, arg in enumerate(args[0]):
            if "|" in arg:
                # the target path is provided
                parts = arg.split("|") 
                base_name = basename(parts[0])
                paths[base_name] = parts[1]
                files[base_name] = open(parts[0], "rb")
            else:    
                base_name = basename(arg)
                files[base_name] = open(arg, "rb")
        got = post(
            url + "/plugins",
            data={"paths": dumps(paths)},
            headers={"authorization": secret, "enctype": "multipart/form-data"},
            files=files,
        )
        return True


def get_lockfile_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        server_key = env["server"]
        server_data = env["server_data"][server_key]
        url = server_data["url"]
        secret = server_data["secret"]
        
        target_file = args[0][0]
        
        got = get(url + "/lockfile", headers={"authorization": secret})
        with open(target_file, "wb") as f:
            f.write(got.content)
        return True


def get_thumbs_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        server_key = env["server"]
        server_data = env["server_data"][server_key]
        url = server_data["url"]
        secret = server_data["secret"]
        target_file = args[0][0]
        
        got = get(url + "/thumbs", headers={"authorization": secret})
        with open(target_file, "wb") as f:
            f.write(got.content)
        return True


def get_log_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        server_key = env["server"]
        server_data = env["server_data"][server_key]
        url = server_data["url"]
        secret = server_data["secret"]
        target_file = args[0][0]
        got = get(url + "/log", headers={"authorization": secret})
        with open(target_file, "wb") as f:
            f.write(got.content)
        return True