from pwinput import pwinput
from subprocess import check_output
from os import path, environ
import random
import string

SECRET_KEY_LENGTH = 50
BASE_DIR = path.dirname(path.realpath(__file__))

questions = [
    {
        "text": "Do you want to use an easy mode (hides values you don't need when running official content)",
        "default": "yes",
        "key": "easy_mode",
        "values": ["yes", "no"],
        "is_hidden": False,
    },
    {
        "text": "Name your username to be used",
        "default": None,
        "key": "user_name",
        "values": [],
        "is_hidden": False,
    },
    {
        "text": "Name your password to be used",
        "default": None,
        "key": "user_pass",
        "values": [],
        "is_hidden": True,
    },
    {
        "text": "Should APX use a global steamcmd instead of one per server? no - recommended",
        "default": "no",
        "key": "global_steam",
        "values": ["yes", "no"],
        "is_hidden": False,
    },
    {
        "text": "Do you want to support the project with adding the prefix '[APX]' to the server names?",
        "default": "yes",
        "key": "add_prefix",
        "values": ["yes", "no"],
        "is_hidden": False,
    },
    {
        "text": "What database should be used? sqlite or mariadb? sqlite - recommended",
        "default": "sqlite",
        "key": "add_prefix",
        "values": ["sqlite", "mariadb"],
        "is_hidden": False,
    },
    {
        "text": "Is APX allowed to speedtest to identify the bandwith (will be done once on startup). Uses speedtest.net in the background.",
        "default": "yes",
        "key": "allow_speedtest",
        "values": ["yes", "no"],
        "is_hidden": False,
    },
]
answers = {}

for question in questions:
    key = question["key"]
    text = question["text"]
    default = question["default"]
    values = question["values"]
    question_text = question["text"] + ": "
    is_hidden = question["is_hidden"]

    reinsert_needed = False
    if len(values) > 0:
        got = input(question["text"] + f" {values}: ")
    else:
        if is_hidden:
            got = pwinput(mask="*")
            repeat = pwinput(prompt="Repeat: ", mask="*")
            if got != repeat:
                print("Passwords do not match!")
                reinsert_needed = True
            else:
                reinsert_needed = False
        else:
            got = input(question_text)

    if not got and default is None:
        answers[key] = default
    while (
        len(values) > 0
        and got.lower() not in values
        or not got
        and default is None
        or reinsert_needed
    ):
        if len(values) > 0:
            print(f"Name a valid option. Options: {values}")
        else:
            print("Name a valid option!")
        if len(values) > 0:
            got = input(question["text"] + f" {values}: ")
        else:
            if is_hidden:
                got = pwinput(prompt="Set password: ", mask="*")
                repeat = pwinput(prompt="Repeat: ", mask="*")
                if got != repeat:
                    print("Passwords do not match!")
                    reinsert_needed = True
                else:
                    reinsert_needed = False
            else:
                got = input(question_text)

    answers[key] = got


settings_tpl_path = path.join(BASE_DIR, "wizard", "settings.py.tpl")

new_content = []
with open(settings_tpl_path, "r", encoding="utf-8") as file:
    content = file.readlines()
    easy_mode = answers["easy_mode"] == "yes"
    global_steam = answers["global_steam"] == "yes"
    add_prefix = answers["add_prefix"] == "yes"
    allow_speedtest = answers["allow_speedtest"] == "yes"
    for line in content:
        if "SECRET_KEY" in line:
            random_key = "".join(
                random.choice(
                    string.ascii_uppercase
                    + string.ascii_lowercase
                    + string.digits
                    + string.punctuation
                )
                for i in range(SECRET_KEY_LENGTH)
            ).replace(
                '"', ""
            )  # make sure we have no string delimiters in there
            line = f'SECRET_KEY = "{random_key}"\n'
        if "DEBUG" in line:
            line = f"DEBUG = False\n"
        if "EASY_MODE" in line:
            line = f"EASY_MODE = {easy_mode}\n"
        if "USE_GLOBAL_STEAMCMD" in line:
            line = f"USE_GLOBAL_STEAMCMD = {global_steam}\n"
        if "ADD_PREFIX" in line:
            line = f"ADD_PREFIX = {add_prefix}\n"
        if "SPEEDTEST_ALLOWED" in line:
            line = f"SPEEDTEST_ALLOWED = {allow_speedtest}\n"
        new_content.append(line)


settings_path = path.join(BASE_DIR, "wizard", "settings.py")

with open(settings_path, "w", encoding="utf-8") as file:
    for line in new_content:
        file.write(line)


django_env = dict(
    environ,
    DJANGO_SUPERUSER_USERNAME=answers["user_name"],
    DJANGO_SUPERUSER_PASSWORD=answers["user_pass"],
)

manage_path = path.join(BASE_DIR, "manage.py")

got = check_output(
    f"python.exe {manage_path} createsuperuser --noinput --email apx@localhost",
    env=django_env,
    shell=True,
).decode("utf-8")
