from django.core.management.base import BaseCommand
from webgui.models import Server, ServerCron, Chat, background_action_chat
from wizard.settings import BASE_DIR
from os.path import join, exists
from os import unlink
from time import sleep


class Command(BaseCommand):
    help = "Executes a given cron job"

    def add_arguments(self, parser):
        parser.add_argument("cron_id", nargs=None, type=int)

    def try_to_obtain_lock(self):
        lock_path = join(BASE_DIR, "cron.lock")
        if exists(lock_path):
            print(f"Lock {lock_path} is existing.")
            for i in range(1, 5):
                print(f"Lock {lock_path} is existing. Waiting...")
                sleep(10)
                if not exists(lock_path):
                    print(f"Lock {lock_path} has gone. Continuing...")
                    break

            if exists(lock_path):
                print(f"Lock {lock_path} is still there. Aborting...")
                raise Exception("Lock still there")

        print(f"Locking {lock_path}")
        with open(lock_path, "w") as file:
            file.write("Silence is golden")

    def handle(self, *args, **options):
        maint_file = join(BASE_DIR, "maint")
        if exists(maint_file):
            raise Exception("Instance is in maintenance mode, aborting")
        try:
            cron_id = options["cron_id"]
            cron_job = ServerCron.objects.get(pk=cron_id)
            self.try_to_obtain_lock()
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
                    server.clean()
                    server.save()
                    if cron_job.message is not None and cron_job.message != "":
                        parts = cron_job.message.split(linesep)
                        for part in parts:
                            message = Chat()
                            message.server = server
                            message.message = part
                            message.save()
                            background_action_chat(message)
        except Exception as e:
            print(e)
        finally:
            lock_path = join(BASE_DIR, "cron.lock")
            unlink(lock_path)
            print(f"Unlocked {lock_path}")
