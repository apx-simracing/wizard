from django.apps import AppConfig
from django.core import management
from django.core.management.commands import loaddata
from threading import Thread
from sys import argv
from time import sleep
from wizard.settings import USE_GLOBAL_STEAMCMD, BASE_DIR
from requests import get
from zipfile import ZipFile
from os.path import join, exists
from subprocess import Popen, PIPE


class WebguiConfig(AppConfig):
    name = "webgui"
    verbose_name = "APX Administration: rFactor 2"

    def ready(self):
        # call cron job module
        steamcmd_folder_path = join(BASE_DIR, "steamcmd")
        if USE_GLOBAL_STEAMCMD and not exists(
            join(steamcmd_folder_path, "steamerrorreporter.exe")
        ):
            # try to bootstrap steamcmd
            print("Attempting do download a global steamcmd")
            steamcmd_path = join(BASE_DIR, "steamcmd.zip")
            r = get("https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip")

            with open(steamcmd_path, "wb") as f:
                f.write(r.content)
            print("Unpacking steamcmd")

            zf = ZipFile(steamcmd_path, "r")
            zf.extractall(steamcmd_folder_path)
            zf.close()
            print("Installing steamcmd")

            command_line = join(BASE_DIR, "steamcmd", "steamcmd.exe") + " +quit"
            p = Popen(
                command_line,
                shell=True,
                stderr=PIPE,
                cwd=steamcmd_folder_path,
            )
            p.wait()
