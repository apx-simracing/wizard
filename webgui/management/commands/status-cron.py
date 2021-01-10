from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server
from os.path import join
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
            server.save()
