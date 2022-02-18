from os import unlink
from os.path import join, exists
from shutil import rmtree
import subprocess
import zipfile
import io
from webgui.models import Server
from psutil import process_iter, AccessDenied, NoSuchProcess
from requests import get
from webgui.util import sanitize_subprocess_path, RECIEVER_DOWNLOAD_FROM
from wizard.settings import CHILDREN_DIR
import logging

logger = logging.getLogger(__name__)


# TODO: communication between wizard and recievers should happen via http except the initial *.bat launch
# TODO: db_object as init param for better decoupling
# NOTE: for future improvements http -> websockets
class Reciever:

    CHILDREN_DIR = CHILDREN_DIR

    def __init__(self, secret):
        self.secret = secret
        self.path = join(self.CHILDREN_DIR, secret)
        self.delete_lock_path = join(self.path, "delete.lock")
        self.update_lock_path = join(self.path, "update.lock")
        self.download_lock_path = join(self.path, "download.lock")
        self.keys_path = join(self.path, "server", "UserData", "ServerKeys.bin")
        self.json_path = join(self.path, "reciever", "server.json")
        self.bat_path = join(self.path, "reciever", "reciever.bat")

    def set_db_status(self, status):
        server_obj = Server.objects.filter(public_secret=self.secret).first()

        if server_obj:
            server_obj.status = status
            server_obj.save()
            logger.info(f"Receiver {self.secret} status set to {status}")
        else:
            logger.warning(
                f"Receiver {self.secret} db object not found for {self.path}"
            )

    def _get_pids(self):
        # TODO: get pids for kill() and is_running() methods
        pass

    def has_python_running(self):
        for process in process_iter(["exe"]):
            if join(self.path, "python.exe") == process.info["exe"]:
                return True
        return False

    def has_bat_running(self):
        for process in process_iter(["cmdline"]):
            if process.info["cmdline"] is not None and self.bat_path in process.info["cmdline"]:
                return True
        return False

    def has_delete_lock(self):
        return exists(self.delete_lock_path)

    def has_update_lock(self):
        return exists(self.update_lock_path)

    def has_download_lock(self):
        return exists(self.download_lock_path)

    def make_download_lock(self):
        with open(self.download_lock_path, "w") as f:
            f.write("download.lock")

    def remove_update_lock(self):
        return unlink(self.update_lock_path)

    def remove_download_lock(self):
        return unlink(self.delete_lock_path)

    def is_ready(self):
        if not exists(self.path):
            logger.info(
                f"Reciever {self.secret} is not ready, path {self.path} does not exist"
            )
            return False
        if not exists(self.keys_path):
            logger.info(
                f"Reciever {self.secret} is not ready, keys in {self.keys_path} do not exist"
            )
            return False
        if not exists(self.json_path):
            logger.info(
                f"Reciever {self.secret} is not ready, server.json in {self.json_path} does not exist"
            )
            return False
        if self.has_update_lock():
            logger.info(f"Reciever {self.secret} is not ready, update.lock found")
            return False
        return True

    def start(self):
        # TODO: when stable redirect stdout to file or NULL
        # check if there is already something running within the directory
        cmd = sanitize_subprocess_path(self.bat_path)

        logger.info(f"Starting {self.secret} reciever server via {self.bat_path}")

        self.set_db_status("Starting reciever")

        try:
            subprocess.Popen(
                cmd,
                # stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.error(e, exc_info=1)
            self.set_db_status(str(e))
            pass

    def update(self):
        logger.info(
            f"Reciever {self.secret} has a update lock, trying to kill reciever. Full path: {self.path}"
        )

        self.kill()

        try:
            self.set_db_status(f"Downloading from {RECIEVER_DOWNLOAD_FROM}")

            r = get(RECIEVER_DOWNLOAD_FROM)
            z = zipfile.ZipFile(io.BytesIO(r.content))

            self.set_db_status(f"Extracting contents to {self.path}")

            z.extractall(self.path)

            self.set_db_status(f"Extracted reciever release to {self.path}")

            self.remove_update_lock()
            self.remove_download_lock()

            self.set_db_status(f"Done updating reciever in {self.path}")

        except Exception as e:
            logger.error(e, exc_info=1)

            self.set_db_status(f"Reciever update failed: {str(e)}")

    def delete(self):
        logger.info(f"Processing to delete reciever {self.secret} in {self.path}")

        if not self.has_delete_lock():
            msg = f"Reciever {self.secret} delete() called in {self.path}, but no delete.lock found"
            logger.critical(msg)
            raise Exception(msg)

        self.kill()

        if exists(self.path):
            rmtree(self.path)
            logger.info(f"Reciever {self.secret} deleted in {self.path}")
        else:
            logger.error(f"Reciever {self.secret} files not found in {self.path}")

    def kill(self):
        logger.info(f"Processing to kill reciever {self.secret} in {self.path}")

        _killed = []

        # https://psutil.readthedocs.io/en/latest/#find-process-by-name
        for process in process_iter(["name", "exe", "cmdline", "cwd", "pid"]):

            process_info = process.info
            process_exe = process_info["exe"]
            process_cmdline = (
                " ".join(process_info["cmdline"])
                if process_info["cmdline"] is not None
                else None
            )
            process_cwd = process_info["cwd"]

            try:

                # TODO: probably process_cmdline check should be enough
                if process_exe is not None and "rFactor2 Dedicated.exe" in process_exe:
                    logger.info("Process is a rF2 dedicated server. Skip.")
                    continue

                elif process_exe is not None and process_exe.startswith(self.path):
                    logger.info(f"Killing process {process} b/c of exe: {process_exe}")

                elif process_cmdline is not None and self.path in process_cmdline:
                    logger.info(
                        f"Killing process {process} b/c of cmdline: {process_cmdline}"
                    )

                elif process_cwd is not None and self.path in process_cwd:
                    logger.info(f"Killing process {process} b/c of cwd: {process_cwd}")
                else:
                    # No reason to kill a process
                    continue

                process.kill()

                _killed.append(process.pid)

                logger.info(f"Killed process: {process_info}")

            except AccessDenied:
                logger.critical(
                    f"Tried to kill a process without permission: {process_info}"
                )

            except NoSuchProcess:
                logger.warning(f"Reciever {self.secret} in {self.path} already dead?")

        self.set_db_status(None)

        if len(_killed) == 0:
            # NOTE: adding this to know if we are doing something unnecessary
            raise Exception(f"Failed to kill receiver {self.secret} in {self.path}")
