from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server, ServerStatustext
from os.path import join, exists
from os import mkdir
from wizard.settings import (
    APX_ROOT,
    MEDIA_ROOT,
    PACKS_ROOT,
    FAILURE_THRESHOLD,
    INSTANCE_NAME,
)
import subprocess
from webgui.util import (
    get_server_hash,
    run_apx_command,
    get_hash,
    get_event_config,
    do_post,
)

from json import dumps


class Command(BaseCommand):
    help = "Recieves status of servers"

    def create_virtual_config(self):
        all_servers = Server.objects.all()
        server_data = {}
        for server in all_servers:
            key = get_server_hash(server.url)
            # we assume that the liveries folder may already be existing
            build_path = join(MEDIA_ROOT, get_hash(str(server.user.pk)), "liveries")
            packs_path = join(PACKS_ROOT, get_hash(str(server.user.pk)))
            templates_path = join(
                MEDIA_ROOT, get_hash(str(server.user.pk)), "templates"
            )
            if not exists(packs_path):
                mkdir(packs_path)

            if not exists(build_path):
                mkdir(build_path)

            if not exists(templates_path):
                mkdir(templates_path)
            server_data[key] = {
                "url": server.url,
                "secret": server.secret,
                "public_ip": server.public_ip,
                "env": {
                    "build_path": build_path,
                    "packs_path": packs_path,
                    "templates_path": templates_path,
                },
            }

        return server_data

    def status_job(self):
        all_servers = Server.objects.filter(
            locked=False, action="", status_failures__lt=FAILURE_THRESHOLD
        )

        # preparation: create "virtual APX config"
        server_config = self.create_virtual_config()
        servers_json_path = join(APX_ROOT, "servers.json")
        with open(servers_json_path, "w") as file:
            file.write(dumps(server_config))

        for server in all_servers:
            secret = server.secret
            url = server.url
            key = get_server_hash(url)
            try:
                got = run_apx_command(key, "--cmd status")
                server.status = got

                text = ServerStatustext()
                text.user = server.user
                text.server = server
                text.status = got
                text.save()
                # download server key, if needed:
                if not server.server_key:
                    try:
                        key_root_path = join(MEDIA_ROOT, "keys", key)
                        if not exists(key_root_path):
                            mkdir(key_root_path)
                        key_path = join(key_root_path, "ServerKeys.bin")
                        relative_path = join("keys", key, "ServerKeys.bin")
                        download_key_command = run_apx_command(
                            key, "--cmd lockfile --args {}".format(key_path)
                        )
                        if exists(key_path):
                            server.server_key = relative_path
                    except:
                        self.stderr.write(
                            self.style.ERROR(
                                "{} does not offer a key".format(server.pk)
                            )
                        )
                        do_post(
                            "[{}]: Server {} - {} does not offer a key".format(
                                INSTANCE_NAME, server.pk, server.name
                            )
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

                        do_post(
                            "[{}]: Server {} - {} unlock failed".format(
                                INSTANCE_NAME, server.pk, server.name
                            )
                        )

                # download the logfile
                log_root_path = join(MEDIA_ROOT, "logs", key)
                if not exists(log_root_path):
                    mkdir(log_root_path)
                log_path = join(log_root_path, "reciever.log")
                relative_path = join("logs", key, "reciever.log")
                try:
                    download_log_command = run_apx_command(
                        key, "--cmd log --args {}".format(log_path)
                    )
                    server.log = relative_path
                except:
                    self.stderr.write(
                        self.style.ERROR("{} logfile download failed".format(server.pk))
                    )

                    do_post(
                        "[{}]: Server {} - {} logfile failed".format(
                            INSTANCE_NAME, server.pk, server.name
                        )
                    )

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        "Failed to recieve status for {}: {}".format(server.pk, e)
                    )
                )
                server.status = None
                server.status_failures = server.status_failures + 1

                do_post(
                    "[{}]: Server {} - {} failed to retrieve status. Fail count is now at {}".format(
                        INSTANCE_NAME, server.pk, server.name, server.status_failures
                    )
                )
            finally:
                server.save()

    def interaction_job(self):
        servers_to_start = Server.objects.filter(
            action="S+", locked=False, status_failures__lt=FAILURE_THRESHOLD
        ).all()

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
                do_post(
                    "[{}]: 🚀 Starting looks complete for {}!".format(
                        INSTANCE_NAME, server.name
                    )
                )
            except Exception as e:
                do_post(
                    "[{}]: 😱 Failed starting server {}: {}".format(
                        INSTANCE_NAME, server.name, str(e)
                    )
                )
                server.action = ""
                server.locked = False
                server.save()

        servers_to_stop = Server.objects.filter(
            action="R-", locked=False, status_failures__lt=FAILURE_THRESHOLD
        ).all()

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
                do_post(
                    "[{}]: 🛑 Stopping looks complete for {}!".format(
                        INSTANCE_NAME, server.name
                    )
                )
            except Exception as e:
                do_post(
                    "[{}]: 😱 Failed to stop server {}: {}".format(
                        INSTANCE_NAME, server.name, str(e)
                    )
                )
                server.action = ""
                server.locked = False
                server.save()

        servers_to_deploy = Server.objects.filter(
            action="D", locked=False, status_failures__lt=FAILURE_THRESHOLD
        ).all()

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
                do_post(
                    "[{}]: 😎 Deployment looks good for {}!".format(
                        INSTANCE_NAME, server.name
                    )
                )
            except Exception as e:
                do_post(
                    "[{}]: 😱 Failed deploying server {}: {}".format(
                        INSTANCE_NAME, server.name, str(e)
                    )
                )
                server.action = ""
                server.locked = False
                server.save()

    def handle(self, *args, **options):
        self.status_job()
        self.interaction_job()
