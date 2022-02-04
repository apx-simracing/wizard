from threading import Thread
from subprocess import Popen, PIPE
import signal
from sys import exit
from os import path
from wizard.settings import (
    MEDIA_PORT,
    STATIC_PORT,
    STATIC_ROOT,
    MEDIA_ROOT,
    WIZARD_PORT,
    LISTEN_IP,
    BASE_DIR,
    SPEEDTEST_ALLOWED,
)
from json import dumps, loads
import speedtest

PATH_MANAGE_PY = path.join(BASE_DIR, "manage.py")
PATH_SPEED_TEST = path.join(BASE_DIR, "networkspeed.txt")
PATH_LOGS = path.join(BASE_DIR, "wizard.log")

threads = []

opened_processes = []


def do_speedtest():
    if path.exists(PATH_SPEED_TEST):
        with open(PATH_SPEED_TEST, "r") as file:
            return loads(file.read())
    else:
        print("Doing speedtest, please wait")
    s = speedtest.Speedtest()
    s.get_best_server()
    result = {
        "upstream": bit_to_mbit(s.upload(threads=1)),
        "downstream": bit_to_mbit(s.download(threads=1)),
    }
    with open(PATH_SPEED_TEST, "w") as file:
        file.write(dumps(result))
    return result


def bit_to_mbit(value: float):
    if value == 0:
        return 0
    return value / 1000000


def start(cmd_line):
    log = open(PATH_LOGS, "a")
    print('Executing "{}"'.format(cmd_line))
    child = Popen(
        cmd_line,
        shell=True,
        stdout=log,
        stderr=log,
    )
    opened_processes.append(child)


def exit_handler(signum, frame):
    print("Received exit")
    for process in opened_processes:
        print("Killing child process with ID{}".format(process.pid))
        process.kill()
    print("See you next time!")
    exit(0)


signal.signal(signal.SIGTERM, exit_handler)
signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGBREAK, exit_handler)


print("    _   _____  __")
print("   /_\ | _ \ \/ /")
print("  / _ \|  _/>  < ")
print(" /_/ \_\_| /_/\_\\")
print("stop debugging, start racing!")
if SPEEDTEST_ALLOWED:
    results = do_speedtest()
    print(
        "Downstream: {} mbit/s, Upstream: {} mbit/s".format(
            results["downstream"], results["upstream"]
        )
    )
else:
    print("No network speed available.")
print("ALWAYS EXIT THIS WINDOW WITH CTRL+C!")
print("We will start following processes:")


start(f'python.exe "{PATH_MANAGE_PY}" runserver {LISTEN_IP}:{WIZARD_PORT}')
start(f'python.exe "{PATH_MANAGE_PY}" children')
start(f'python.exe "{PATH_MANAGE_PY}" collectstatic --noinput')
start(f'python.exe -m http.server "{STATIC_PORT}" --directory "{STATIC_ROOT}"')
start(f'python.exe -m http.server "{MEDIA_PORT}" --directory "{MEDIA_ROOT}"')
print("Ready")

try:
    while True:
        pass
    # idea: https://stackoverflow.com/questions/22565606/python-asynhronously-print-stdout-from-multiple-subprocesses
except KeyboardInterrupt:
    print("Exiting")
