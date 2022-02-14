from os.path import exists
from os import listdir
from time import sleep
from django.core.management.base import BaseCommand
from webgui.recievers import Reciever
from wizard.settings import CHILDREN_DIR
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Makes sure client recievers are running"

    def kill_recievers(self):
        if not exists(CHILDREN_DIR):
            logger.info(f"Nothing to kill or servers not in {CHILDREN_DIR}. Exiting...")
            return

        for secret in listdir(CHILDREN_DIR):
            Reciever(secret).kill()

    def handle(self, *args, **options):
        try:
            # TODO: while loop is blocking, async flow could be necessary if many children
            while True:

                if not exists(CHILDREN_DIR):
                    sleep(10)
                    continue

                for secret in listdir(CHILDREN_DIR):

                    reciever = Reciever(secret)

                    if reciever.has_delete_lock():
                        reciever.delete()
                        continue

                    if reciever.has_update_lock():
                        # TODO: update only if there is no download lock???
                        # what if there is both locks, but the process failed?
                        # another state necessary???
                        if not reciever.has_download_lock():
                            reciever.make_download_lock()
                            reciever.update()
                        continue

                    if reciever.has_python_running():
                        logger.info(
                            f"Reciever {reciever.secret} has python.exe running. Let it be."
                        )
                        continue

                    if reciever.is_ready():
                        reciever.start()

                sleep(5)

        except KeyboardInterrupt:
            # kill child processes, if needed
            self.kill_recievers()
