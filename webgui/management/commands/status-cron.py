from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server
from os.path import join, exists
from os import mkdir
from wizard.settings import APX_ROOT, MEDIA_ROOT, PACKS_ROOT
import subprocess
from webgui.util import get_server_hash, run_apx_command

from json import dumps


class Command(BaseCommand):
    help = "Recieves status of servers"

    def create_virtual_config(self):
        all_servers = Server.objects.all()
        server_data = {}
        for server in all_servers:
            key = get_server_hash(server.url)
            server_data[key] = {
                "url": server.url,
                "secret": server.secret,
                "public_ip": server.public_ip,
                "env": {"build_path": MEDIA_ROOT, "packs_path": PACKS_ROOT},
            }

        return server_data

    def handle(self, *args, **options):
        all_servers = Server.objects.all()

        # preparation: create "virtual APX config"
        server_config = self.create_virtual_config()
        servers_json_path = join(APX_ROOT, "servers.json")
        with open(servers_json_path, "w") as file:
            file.write(dumps(server_config))

        for server in all_servers:
            secret = server.secret
            url = server.url
            key = get_server_hash(url)
            got = run_apx_command(key, "--cmd status")
            server.status = got
            # download server key, if needed:
            if not server.server_key:
                try:
                    key_root_path = join(MEDIA_ROOT, "keys", str(server.pk))
                    if not exists(key_root_path):
                        mkdir(key_root_path)
                    key_path = join(key_root_path, "ServerKeys.bin")
                    relative_path = join("keys", str(server.pk), "ServerKeys.bin")
                    download_key_command = run_apx_command(
                        key, "--cmd lockfile --args {}".format(key_path)
                    )
                    if exists(key_path):
                        server.server_key = relative_path
                except:
                    self.stderr.write(
                        self.style.ERROR("{} does not offer a key".format(server.pk))
                    )

            # if an unlock key is present - attempt unlock!
            if server.server_unlock_key:
                try:
                    key_root_path = join(MEDIA_ROOT, server.server_unlock_key.name)
                    download_key_command = run_apx_command(
                        key, "--cmd unlock --args {}".format(key_root_path)
                    )
                    server.server_unlock_key = None
                except:
                    self.stderr.write(
                        self.style.ERROR("{} unlock failed".format(server.pk))
                    )

            server.save()
