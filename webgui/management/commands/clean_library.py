from posixpath import islink
from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server
from os.path import join, exists
from shutil import rmtree
from os import mkdir, listdir, unlink, readlink
from wizard.settings import (
    LIBRARY_PATH,
    BASE_DIR
)
import subprocess
from webgui.util import RECIEVER_DOWNLOAD_FROM
from time import sleep
import zipfile, io
from psutil import process_iter
from requests import get


class Command(BaseCommand):
    help = "Removes folders not needed from the library"

    def handle(self, *args, **options):
      server_children_root = join(BASE_DIR, "server_children")
      servers = listdir(server_children_root)
      for server in servers:
        self.investigate_server(join(server_children_root, server))
    def investigate_server(self, server_path):
      installed_root = join(server_path, "Installed")
      types = ["Vehicles", "Locations"]
      ignore = ["Clio_PC", "CorvettePC", "CorvettePCLights"]
      used = []
      for mod_type in types:
        full_type_path = join(installed_root, mod_type)
        mods = listdir(full_type_path)
        for mod in mods:
          if mod not in ignore:
            print(f"Found mod {mod}")
            full_mod_path = join(full_type_path, mod)
            versions = listdir(full_mod_path)
            for version in versions:
              full_version_path = join(full_mod_path, version)
              library_path = join(LIBRARY_PATH, mod, version)
              if exists(library_path):
                used.append(join(mod, version))

      library_mods = listdir(LIBRARY_PATH)
      removal_candidates = []
      for mod in library_mods:
        if mod != "server": # ignore the server template
          versions = listdir(join(LIBRARY_PATH, mod))
          for version in versions:
            needle = join(mod, version)
            if needle not in used:
              removal_candidates.append(join(mod, version))
      for removal_canidate in removal_candidates:
        full_path = join(LIBRARY_PATH, removal_canidate)
        rmtree(full_path)
        print(f"Removed {full_path}")