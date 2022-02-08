from django.core.management.base import BaseCommand
from webgui.models import (
    ServerCron,
    Chat,
    background_action_chat,
    do_server_interaction,
)
from wizard.settings import BASE_DIR
from os.path import join, exists
from os import unlink
from time import sleep
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Executes a given cron job"

    def add_arguments(self, parser):
        parser.add_argument("cron_id", nargs=None, type=int)

    def try_to_obtain_lock(self):
        lock_path = join(BASE_DIR, "cron.lock")
        if exists(lock_path):
            logger.info(f"Lock {lock_path} is existing.")
            for i in range(1, 5):
                logger.info(f"Lock {lock_path} is existing. Waiting...")
                sleep(10)
                if not exists(lock_path):
                    logger.info(f"Lock {lock_path} has gone. Continuing...")
                    break

            if exists(lock_path):
                logger.info(f"Lock {lock_path} is still there. Aborting...")
                raise Exception("Lock still there")

        logger.info(f"Locking {lock_path}")
        with open(lock_path, "w") as file:
            file.write("Silence is golden")

    def handle(self, *args, **options):
        maint_file = join(BASE_DIR, "maint")
        got_lock = False
        if exists(maint_file):
            msg = "Instance is in maintenance mode, aborting"
            logger.warning(msg)
            raise Exception(msg)
        try:
            cron_id = options["cron_id"]
            cron_job = ServerCron.objects.get(pk=cron_id)
            logger.info(f"Desired job description: {cron_job}")
            self.try_to_obtain_lock()
            got_lock = True
            server = cron_job.server
            server.action = cron_job.action
            only_when_practice = cron_job.apply_only_if_practice
            if (
                not only_when_practice
                or only_when_practice
                and server.status is not None
                and '"session": "PRACTICE1"' in server.status
            ):
                if cron_job.event is not None:
                    server.event = cron_job.event
                server.save()
                do_server_interaction(server)
                if cron_job.message is not None and cron_job.message != "":
                    # FIXME: "linesep" is not defined
                    parts = cron_job.message.split(linesep)
                    for part in parts:
                        message = Chat()
                        message.server = server
                        message.message = part
                        message.save()
                        background_action_chat(message)
        except Exception as e:
            logger.error(e, exc_info=1)
        finally:
            if got_lock:
                lock_path = join(BASE_DIR, "cron.lock")
                unlink(lock_path)
                logger.info(f"Unlocked {lock_path}")
