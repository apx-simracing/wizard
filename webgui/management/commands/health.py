from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server, User
from os.path import join, exists
from os import mkdir
from wizard.settings import (
    APX_ROOT,
    MEDIA_ROOT,
    PACKS_ROOT,
    FAILURE_THRESHOLD,
    INSTANCE_NAME,
)
from webgui.util import do_post
from pathlib import Path


class Command(BaseCommand):
    help = "Recieves status of the overall system"

    def folder_size_mb(self, path):
        root_directory = Path(path)
        upload_size = round(
            sum(f.stat().st_size for f in root_directory.glob("**/*") if f.is_file())
            / 1024
            / 1024,
            2,
        )
        return upload_size

    def handle(self, *args, **options):
        users = User.objects.all()
        servers = Server.objects.all()
        servers_fail = Server.objects.filter(status_failures__gt=0)
        servers_fail_threshold = Server.objects.filter(
            status_failures__gte=FAILURE_THRESHOLD
        )
        upload_size = self.folder_size_mb(MEDIA_ROOT)
        packs_size = self.folder_size_mb(PACKS_ROOT)
        message = "[{}]: 👨‍⚕️ {} Users, {} Servers ({} with failures, {} ignored because of threshold), Uploads: {} MB, Packs: {} MB".format(
            INSTANCE_NAME,
            len(users),
            len(servers),
            len(servers_fail),
            len(servers_fail_threshold),
            upload_size,
            packs_size,
        )
        do_post(message)
        print(message)
