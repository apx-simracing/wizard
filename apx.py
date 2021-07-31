from threading import Thread
from subprocess import Popen, PIPE
import signal
from sys import exit
from wizard.settings import MEDIA_PORT, STATIC_PORT, WIZARD_PORT, LISTEN_IP

threads = []

opened_processes = []


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
print("ALWAYS EXIT THIS WINDOW WITH CTRL+C!")
print("We will start following processes:")


start(f"python.exe manage.py runserver {LISTEN_IP}:{WIZARD_PORT}")
start("python.exe manage.py children")
start("python.exe manage.py collectstatic --noinput")
start(f"python.exe -m http.server {STATIC_PORT} --directory ./static")
start(f"python.exe -m http.server {MEDIA_PORT} --directory ./uploads")
print("Ready")

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting")
