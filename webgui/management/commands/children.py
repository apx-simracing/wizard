from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server
from os.path import join, exists
from shutil import rmtree
from os import listdir, unlink
from wizard.settings import (
    # APX_ROOT,
    # MEDIA_ROOT,
    # PACKS_ROOT,
    # FAILURE_THRESHOLD,
    # INSTANCE_NAME,
    BASE_DIR,
)
import subprocess
from webgui.util import RECIEVER_DOWNLOAD_FROM
from time import sleep
import zipfile, io
from psutil import process_iter
from requests import get


PATH_CHILDREN = join(BASE_DIR, "server_children")

class Command(BaseCommand):
    help = "Makes sure client recievers are running"

    def kill_children(self):

        if not exists(PATH_CHILDREN):
            print(f"Nothing to kill or servers not in {PATH_CHILDREN}. Exiting...")
            return

        folders = listdir(PATH_CHILDREN)
        for secret in folders:
            print("Processing {} to exit...".format(secret))
            server_obj = Server.objects.filter(public_secret=secret).first()
            if server_obj:
                server_obj.status = None
                server_obj.save()

            expected_path = join(PATH_CHILDREN, secret)
            # TODO: SOMETHING IS STILL STRANGE HERE
            # something_running = False
            for process in process_iter():
                try:
                    path = process.exe()
                    if "rFactor2 Dedicated.exe" not in path:
                        if path.startswith(expected_path):
                            print(
                                "Killing process {} b/c of origin path".format(process)
                            )
                            process.kill()
                        # find the cmd
                        cmd_line = process.cwd()
                        if expected_path in cmd_line:
                            print("Killing process {} b/c of cwd path".format(process))
                            process.kill()
                    else:
                        print("There is an server running. This is not our job.")
                except Exception as e:
                    pass  # there will be a lot of access denied messages

    def handle(self, *args, **options):
        try:
            while True:
                
                sleep(5)

                if not exists(PATH_CHILDREN):
                    # let's sleep a bit more
                    sleep(10)
                    continue

                folders = listdir(PATH_CHILDREN)
                for secret in folders:
                    server_obj = Server.objects.filter(public_secret=secret).first()
                    if server_obj:
                        server_obj.status = None
                        server_obj.save()

                    expected_path = join(
                        PATH_CHILDREN, secret, "python.exe"
                    )

                    path = join(PATH_CHILDREN, secret)
                    # TODO: SOMETHING IS STILL STRANGE HERE
                    something_running = False

                    delete_lock = join(
                        PATH_CHILDREN,
                        secret,
                        "delete.lock",
                    )
                    update_lock = join(
                        PATH_CHILDREN,
                        secret,
                        "update.lock",
                    )
                    if not exists(delete_lock):
                        for process in process_iter():
                            try:
                                process_path = process.exe()
                                if expected_path == process_path:
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
                            keys = join(
                                PATH_CHILDREN,
                                secret,
                                "server",
                                "UserData",
                                "ServerKeys.bin",
                            )
                            server_json = join(
                                PATH_CHILDREN,
                                secret,
                                "reciever",
                                "server.json",
                            )
                            batch_path_cwd = join(
                                PATH_CHILDREN, secret, "reciever"
                            )
                            batch_path = join(
                                PATH_CHILDREN,
                                secret,
                                "reciever",
                                "reciever.bat",
                            )
                            if (
                                exists(path)
                                and exists(keys)
                                and exists(server_json)
                                and not exists(update_lock)
                            ):
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
                    if exists(update_lock):
                        download_lock = join(
                            PATH_CHILDREN,
                            secret,
                            "download.lock",
                        )
                        if not exists(download_lock):
                            with open(download_lock, "w") as file:
                                file.write("locking download")
                            try:
                                print(
                                    "Server {} has a update lock, trying to kill reciever. Full path: {}".format(
                                        secret, path
                                    )
                                )
                                for process in process_iter():
                                    try:
                                        process_path = process.exe()
                                        if process_path.startswith(path):
                                            print("killing", process_path)
                                            process.kill()
                                        cmd_line = process.cwd()
                                        expected_path = join(
                                            PATH_CHILDREN, secret
                                        )
                                        if expected_path in cmd_line:
                                            print(
                                                "Killing process {} b/c of cwd path".format(
                                                    process
                                                )
                                            )
                                            process.kill()

                                    except:
                                        pass
                                # attempt update
                                try:
                                    server_obj.state = "Downloading {}".format(
                                        RECIEVER_DOWNLOAD_FROM
                                    )
                                    server_obj.save()
                                    r = get(RECIEVER_DOWNLOAD_FROM)
                                    z = zipfile.ZipFile(io.BytesIO(r.content))
                                    server_obj.state = (
                                        f"Extracting contents to {path}"
                                    )
                                    print(f"Extracting contents to {path}")
                                    server_obj.save()
                                    z.extractall(path)
                                    server_obj.state = "Extracted reciever release"
                                    server_obj.save()
                                    unlink(update_lock)
                                    unlink(download_lock)
                                    server_obj.state = "Done updating reciever"
                                    server_obj.save()
                                except Exception as e:
                                    server_obj.state = (
                                        "Download for reciever failed: {}".format(e)
                                    )
                                    server_obj.save()
                            except Exception as e:
                                print(
                                    "Server {} has a update lock, but I failed".format(
                                        secret
                                    )
                                )
                                server_obj.state = (
                                    "Something went wrong: {}".format(e)
                                )
                                server_obj.save()
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
                                    cmd_line = process.cwd()
                                    expected_path = join(
                                        PATH_CHILDREN, secret
                                    )
                                    if expected_path in cmd_line:
                                        print(
                                            "Killing process {} b/c of cwd path".format(
                                                process
                                            )
                                        )
                                        process.kill()
                                except:
                                    pass
                            if exists(path):
                                rmtree(path)
                        except:
                            print(
                                "Server {} has a delete lock, but I failed".format(
                                    secret
                                )
                            )
        except KeyboardInterrupt:
            # kill child processes, if needed
            self.kill_children()
