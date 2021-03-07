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
    CRON_CHUNK_SIZE,
    CRON_TIMEOUT,
    CRON_THREAD_KILL_TIMEOUT,
)
import subprocess
from webgui.util import (
    get_server_hash,
    run_apx_command,
    get_hash,
    get_event_config,
    do_post,
)
from django.db.models.signals import post_save

from django.dispatch import receiver
from json import dumps
from time import sleep
from threading import Thread, get_ident


class Command(BaseCommand):
    help = "Recieves status of servers"
    kill_all_threads = False

    def status_job(servers: list):
        all_servers = Server.objects.filter(
            pk__in=servers,
            locked=False,
            status_failures__lt=FAILURE_THRESHOLD,
        )

        for server in all_servers:
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
                        print("{} does not offer a key".format(server.pk))
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

                        print("{} unlock failed".format(server.pk))

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
                    print("{} logfile download failed".format(server.pk))

                    do_post(
                        "[{}]: Server {} - {} logfile failed".format(
                            INSTANCE_NAME, server.pk, server.name
                        )
                    )

            except Exception as e:
                print("Failed to recieve status for {}: {}".format(server.pk, e))
                server.status = None
                server.status_failures = server.status_failures + 1

                do_post(
                    "[{}]: Server {} - {} failed to retrieve status. Fail count is now at {}".format(
                        INSTANCE_NAME, server.pk, server.name, server.status_failures
                    )
                )
            finally:
                server.save()

    def thread_action(servers):
        print("Thread {} action start".format(get_ident()))
        while not Command.kill_all_threads:
            Command.status_job(servers)
            sleep(CRON_TIMEOUT)
        print("Thread {} action end".format(get_ident()))

    def chunks(lst, n):
        # https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    def chunk_list():
        Command.kill_all_threads = False
        servers = Server.objects.filter(
            status_failures__lt=FAILURE_THRESHOLD
        ).values_list("pk", flat=True)

        server_chunks = list(Command.chunks(servers, CRON_CHUNK_SIZE))
        threads = []
        for servers in server_chunks:
            chunk_thread = Thread(
                target=Command.thread_action, args=(servers,), daemon=True
            )
            threads.append(chunk_thread)
            chunk_thread.start()

        return threads

    def handle(self, *args, **options):
        try:
            print("Chunking servers to allow new and changed servers to be included")
            threads = Command.chunk_list()
            sleep(CRON_THREAD_KILL_TIMEOUT)
            Command.kill_all_threads = True
            for thread in threads:
                thread.join()
            print("Exiting")

        except KeyboardInterrupt:
            Command.kill_all_threads = True
