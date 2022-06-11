from threading import Thread
from subprocess import Popen, PIPE
import signal
from sys import exit
from os.path import join, exists
from termcolor import colored
from psutil import process_iter
from wizard.settings import (
    MEDIA_PORT,
    STATIC_PORT,
    WIZARD_PORT,
    LISTEN_IP,
    BASE_DIR,
    SPEEDTEST_ALLOWED,
)
from json import dumps, loads
import speedtest

threads = []

opened_processes = []


def do_speedtest():
    speed_file_path = join(BASE_DIR, "networkspeed.txt")
    if exists(speed_file_path):
        with open(speed_file_path, "r") as file:
            return loads(file.read())
    else:
        print("Doing speedtest, please wait")
    s = speedtest.Speedtest()
    s.get_best_server()
    result = {
        "upstream": bit_to_mbit(s.upload(threads=1)),
        "downstream": bit_to_mbit(s.download(threads=1)),
    }
    with open(speed_file_path, "w") as file:
        file.write(dumps(result))
    return result


def bit_to_mbit(value: float):
    if value == 0:
        return 0
    return value / 1000000


def start(cmd_line):
    log = open("wizard.log", "a")
    print('Executing "{}"'.format(cmd_line))
    child = Popen(
        cmd_line,
        shell=True,
        stdout=log,
        stderr=log,
    )
    opened_processes.append(child)


def is_steam_running():
    for process in process_iter():
        try:
            path = process.exe()
            if "steam.exe" in path:
               return True
        except Exception as e:
            pass  # there will be a lot of access dened messages
    return False
def exit_handler(signum, frame):
    print("Recieved exit")
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


start(f"python.exe manage.py runserver {LISTEN_IP}:{WIZARD_PORT}")
start("python.exe manage.py children")
start("python.exe manage.py collectstatic --noinput")
start(f"python.exe -m http.server {STATIC_PORT} --directory ./static")
start(f"python.exe -m http.server {MEDIA_PORT} --directory ./uploads")

if is_steam_running():
    print("{}: We detected a running Steam client. Follow this steps if Server and Game are located on the same PC.".format(colored("Warning", "red")))
    print("1. Close Steam")
    print("2. Start APX (AND your servers)")
    print("3. Start steam and rFactor 2")
    print(colored("APX will exit now.", "red"))
    exit_handler(None, None)
    exit(1)
else:
    print(colored("No steam running. No actions needed", "green"))
print("Ready")

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting")
