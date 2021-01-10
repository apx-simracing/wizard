from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server
from os.path import join
from wizard.settings import APX_ROOT, MEDIA_ROOT
import subprocess
from webgui.util import get_server_hash, run_apx_command, get_event_config

from json import dumps


class Command(BaseCommand):
    help = "Interacts with a given server"

    def handle(self, *args, **options):
        servers_to_start = Server.objects.filter(action="S+").all()

        for server in servers_to_start:
            secret = server.secret
            url = server.url
            key = get_server_hash(url)
            try:
                server.locked = True
                server.save()
                run_apx_command(key, "--cmd start")
                server.action = ""
                server.locked = False
                server.save()
            except:
                pass

        servers_to_stop = Server.objects.filter(action="R-").all()

        for server in servers_to_stop:
            secret = server.secret
            url = server.url
            key = get_server_hash(url)
            try:
                server.locked = True
                server.save()
                run_apx_command(key, "--cmd stop")
                server.action = ""
                server.locked = False
                server.save()
            except:
                pass

        servers_to_deploy = Server.objects.filter(action="D").all()

        for server in servers_to_deploy:
            secret = server.secret
            url = server.url
            key = get_server_hash(url)

            # save event json
            event_config = get_event_config(server.event.pk)
            config_path = join(APX_ROOT, "configs", key + ".json")
            with open(config_path, "w") as file:
                file.write(dumps(event_config))
            # save rfm
            rfm_path = join(MEDIA_ROOT, server.event.conditions.rfm.name)

            try:
                server.locked = True
                server.save()
                command_line = "--cmd build_skins --args {} {}".format(
                    config_path, rfm_path
                )
                run_apx_command(key, command_line)
                command_line = "--cmd deploy --args {} {}".format(config_path, rfm_path)
                run_apx_command(key, command_line)
                server.action = ""
                server.locked = False
                server.save()
            except:
                pass
