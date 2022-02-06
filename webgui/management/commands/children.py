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
    CHILDREN_DIR
)
import subprocess
from webgui.util import sanitize_subprocess_path, RECIEVER_DOWNLOAD_FROM
from time import sleep
import zipfile, io
from psutil import process_iter, AccessDenied
from requests import get
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Makes sure client recievers are running"

    def kill_children(self):

        if not exists(CHILDREN_DIR):
            logger.info(f"Nothing to kill or servers not in {CHILDREN_DIR}. Exiting...")
            return

        folders = listdir(CHILDREN_DIR)
        for secret in folders:
            logger.info("Processing {} to exit...".format(secret))
            server_obj = Server.objects.filter(public_secret=secret).first()
            if server_obj:
                server_obj.status = None
                server_obj.save()

            expected_path = join(CHILDREN_DIR, secret)
            # TODO: SOMETHING IS STILL STRANGE HERE
            # something_running = False
            for process in process_iter():
                try:
                    path = process.exe()
                    if "rFactor2 Dedicated.exe" not in path:
                        if path.startswith(expected_path):
                            logger.info(
                                "Killing process {} b/c of origin path".format(process)
                            )
                            process.kill()
                        # find the cmd
                        cmd_line = process.cwd()
                        if expected_path in cmd_line:
                            logger.info("Killing process {} b/c of cwd path".format(process))
                            process.kill()
                    else:
                        logger.info("There is an server running. This is not our job.")
                except AccessDenied as e:
                    logger.warning(str(e))
                    pass  # there will be a lot of access denied messages

    def handle(self, *args, **options):
        try:
            while True:
                
                sleep(5)

                if not exists(CHILDREN_DIR):
                    # let's sleep a bit more
                    sleep(10)
                    continue

                folders = listdir(CHILDREN_DIR)
                for secret in folders:
                    server_obj = Server.objects.filter(public_secret=secret).first()
                    if server_obj:
                        server_obj.status = None
                        server_obj.save()

                    expected_path = join(
                        CHILDREN_DIR, secret, "python.exe"
                    )

                    path = join(CHILDREN_DIR, secret)
                    # TODO: SOMETHING IS STILL STRANGE HERE
                    something_running = False

                    delete_lock = join(
                        CHILDREN_DIR,
                        secret,
                        "delete.lock",
                    )
                    update_lock = join(
                        CHILDREN_DIR,
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
                            logger.info(
                                "Server {} has running something. Will not be altered.".format(
                                    secret
                                )
                            )

                        if not something_running:
                            keys = join(
                                CHILDREN_DIR,
                                secret,
                                "server",
                                "UserData",
                                "ServerKeys.bin",
                            )
                            server_json = join(
                                CHILDREN_DIR,
                                secret,
                                "reciever",
                                "server.json",
                            )
                            batch_path_cwd = join(
                                CHILDREN_DIR, secret, "reciever\\"
                            )
                            batch_path = join(
                                CHILDREN_DIR,
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
                                # TODO: python win path with space issue
                                # check if there is already something running within the directory
                                logger.info("Server {} needs start".format(secret))
                                cmd = sanitize_subprocess_path(batch_path)
                                # cwd = sanitize_subprocess_path(batch_path_cwd)
                                # cmd = batch_path
                                cwd = batch_path_cwd
                                try:
                                    subprocess.Popen(
                                        cmd,
                                        cwd=cwd,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                    )
                                except Exception as e:
                                    logger.error(f"cmd={cmd} cwd={cwd}")
                                    logger.error(str(e), exc_info=True)
                                    # Exceptions can't really handled at this point, so we are ignoring them
                                    pass
                            else:
                                logger.info(
                                    "Server {} needs start, but is not finished deploying".format(
                                        secret
                                    )
                                )
                    if exists(update_lock):
                        download_lock = join(
                            CHILDREN_DIR,
                            secret,
                            "download.lock",
                        )
                        if not exists(download_lock):
                            with open(download_lock, "w") as file:
                                file.write("locking download")
                            try:
                                logger.info(
                                    "Server {} has a update lock, trying to kill reciever. Full path: {}".format(
                                        secret, path
                                    )
                                )
                                for process in process_iter():
                                    try:
                                        process_path = process.exe()
                                        if process_path.startswith(path):
                                            logger.info("killing", process_path)
                                            process.kill()
                                        cmd_line = process.cwd()
                                        expected_path = join(
                                            CHILDREN_DIR, secret
                                        )
                                        if expected_path in cmd_line:
                                            logger.info(
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
                                    logger.info(f"Extracting contents to {path}")
                                    server_obj.save()
                                    z.extractall(path)
                                    server_obj.state = "Extracted reciever release"
                                    server_obj.save()
                                    unlink(update_lock)
                                    unlink(download_lock)
                                    server_obj.state = "Done updating reciever"
                                    server_obj.save()
                                except Exception as e:
                                    logger.error(str(e), exc_info=True)
                                    server_obj.state = (
                                        "Download for reciever failed: {}".format(e)
                                    )
                                    server_obj.save()
                            except Exception as e:
                                logger.error(
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
                            logger.info(
                                "Server {} has a delete lock. Full path: {}".format(
                                    secret, path
                                )
                            )
                            for process in process_iter():
                                try:
                                    process_path = process.exe()
                                    if process_path.startswith(path):
                                        logger.info(f"killing: {process_path}")
                                        process.kill()
                                    cmd_line = process.cwd()
                                    expected_path = join(
                                        CHILDREN_DIR, secret
                                    )
                                    if expected_path in cmd_line:
                                        logger.info(
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
                            logger.error(f"Server {secret} has a delete lock, but I failed")
        except KeyboardInterrupt:
            # kill child processes, if needed
            self.kill_children()
