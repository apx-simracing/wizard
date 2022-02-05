from requests import get
import logging

logger = logging.getLogger(__name__)


def get_status_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        logger.info(background_status(env))
        return True


def background_status(env):
    server_key = env["server"]
    server_data = env["server_data"][server_key]
    url = server_data["url"]
    secret = server_data["secret"]
    got = get(
        url + "/status",
        headers={
            "authorization": secret,
            "content-type": "application/x-www-form-urlencoded",
        },
    )
    return got.text


def get_drivers_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        got = background_status(env)
        if got:
            vehicles = got["vehicles"]

            mapped_vehicles = list(
                map(
                    lambda v: {
                        "driver": v["driverName"],
                        "vehicle": v["vehicleName"],
                        "penalties": v["penalties"],
                        "pitstops": v["pitstops"],
                        "lapDistance": v["lapDistance"],
                        "vehicleClass": v["carClass"],
                        "steamID": v["steamID"] if v["steamID"] != 0 else None,
                    },
                    vehicles,
                )
            )
            logger.info(mapped_vehicles)
        else:
            return False
    return True


def get_states_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        got = background_status(env)
        logger.info(got["states"])
