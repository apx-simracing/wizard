from .util import http_api_helper
import logging

logger = logging.getLogger(__name__)


def chat_command(env, *args, **kwargs) -> bool:
    got, text = http_api_helper(env, "chat", {
        "message": ' '.join(args[0])
    })
    logger.info(text)
    return got


def kick_command(env, *args, **kwargs) -> bool:
    driver = args[0]
    if len(driver) != 1:
        return False
    got, text = http_api_helper(env, "kick", {
        "driver": driver
    })
    logger.info(text)
    return got


def rejoin_driver_command(env, *args, **kwargs) -> bool:
    got_dq, dq_text = http_api_helper(env, "chat", {
        "message": "/dq " + ' '.join(args[0])
    })
    got_undq, undq_text = http_api_helper(env, "chat", {
        "message": "/undq " + ' '.join(args[0])
    })
    logger.info(dq_text)
    logger.info(undq_text)
    return got_dq and got_undq


def action_helper(env, action: str):
    got, text = http_api_helper(env, "/action/" + action, {})
    logger.info(text)
    return got


def add_bot_command(env, *args, **kwargs):
    return action_helper(env, "addbot")


def restart_weekend_command(env, *args, **kwargs):
    return action_helper(env, "RESTARTWEEKEND")


def restart_race_command(env, *args, **kwargs):
    return action_helper(env, "RESTARTRACE")


def next_session_command(env, *args, **kwargs):
    return action_helper(env, "NEXTSESSION")
