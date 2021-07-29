from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server
from os.path import join, exists
from shutil import rmtree
from os import mkdir, listdir
from wizard.settings import (
    APX_ROOT,
    MEDIA_ROOT,
    PACKS_ROOT,
    FAILURE_THRESHOLD,
    INSTANCE_NAME,
    CRON_CHUNK_SIZE,
    CRON_TIMEOUT,
    CRON_THREAD_KILL_TIMEOUT,
    CRON_TIMEZONE,
    BASE_DIR,
)
import subprocess
from time import sleep

from psutil import process_iter


class Command(BaseCommand):
    help = "Makes sure client reciegers are running"

    def handle(self, *args, **options):
        while True:
            sleep(5)
            servers = Server.objects.all()
            root_path = join(BASE_DIR, "server_children")
            folders = listdir(root_path)
            for secret in folders:
                print("Processing {}...".format(secret))
                expected_path = join(BASE_DIR, "server_children", secret, "python.exe")
                something_running = False

                delete_lock = join(
                    BASE_DIR,
                    "server_children",
                    secret,
                    "delete.lock",
                )
                if not exists(delete_lock):
                    for process in process_iter():
                        try:
                            path = process.exe()
                            if expected_path == path:
                                something_running = True
                                break
                        except:
                            pass
                    if something_running:
                        print(
                            "Server {} has running something. Will not be altered.".format(
                                secret
                            )
                        )
                    if not something_running:
                        path = join(BASE_DIR, "server_children", secret)
                        keys = join(
                            BASE_DIR,
                            "server_children",
                            secret,
                            "server",
                            "UserData",
                            "ServerKeys.bin",
                        )
                        server_json = join(
                            BASE_DIR,
                            "server_children",
                            secret,
                            "reciever",
                            "server.json",
                        )
                        batch_path_cwd = join(
                            BASE_DIR, "server_children", secret, "reciever"
                        )
                        batch_path = join(
                            BASE_DIR,
                            "server_children",
                            secret,
                            "reciever",
                            "reciever.bat",
                        )
                        if exists(path) and exists(keys) and exists(server_json):
                            # check if there is already something running within the directory
                            print("Server {} needs start".format(secret))
                            try:
                                subprocess.Popen(
                                    batch_path,
                                    cwd=batch_path_cwd,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                )
                            except Exception as e:
                                print(e)
                                # Exceptions can't really handled at this point, so we are ignoring them
                                pass
                        else:
                            print(
                                "Server {} needs start, but is not finished deploying".format(
                                    secret
                                )
                            )
                if exists(delete_lock):
                    try:
                        print(
                            "Server {} has a delete lock. Full path: {}".format(
                                secret, path
                            )
                        )
                        for process in process_iter():
                            try:
                                process_path = process.exe()
                                if process_path.startswith(path):
                                    print("killing", process_path)
                                    process.kill()
                            except:
                                pass
                        if exists(path):
                            rmtree(path)
                    except:
                        print(
                            "Server {} has a delete lock, but I failed. Full path: {}".format(
                                secret, path
                            )
                        )