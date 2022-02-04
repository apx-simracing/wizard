from typing import Union
from requests import post


def http_api_helper(env: dict, route: str, data: dict, method=post) -> Union[bool, str]:
    if "server_data" not in env or env["server"] not in env["server_data"]:
        raise Exception("Server.json invalid")
    result_ok = False
    result_text = None
    secret = env["server_data"][env["server"]]["secret"]
    url = env["server_data"][env["server"]]["url"]
    try:
        got = method(
            url + f"/{route}",
            headers={
                "authorization": secret,
                "content-type": "application/x-www-form-urlencoded",
            },
            data=data,
        )

        result_ok = got.status_code == 200
        result_text = got.text
    except Exception as err:
        print(result_text)
        result_ok = False
        result_text = str(err)

    return result_ok, result_text
