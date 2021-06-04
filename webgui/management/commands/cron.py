from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server, ServerStatustext, ServerCron
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
    CRON_TIMEZONE,
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
from json import dumps, loads
from time import sleep
from threading import Thread, get_ident
from croniter import croniter
from datetime import datetime
import pytz


class Command(BaseCommand):
    help = "Recieves status of servers"

    def handle(self, *args, **options):
        time_zone = pytz.timezone(CRON_TIMEZONE)
        try:
            cron_jobs = ServerCron.objects.all()
            local_date = time_zone.localize(datetime.now())
            for cron_job in cron_jobs:
                try:
                    cron = cron_job.cron_text
                    next_iteration = croniter(cron, local_date).get_next(datetime)
                    delta = next_iteration - local_date
                    if delta.total_seconds() < CRON_THREAD_KILL_TIMEOUT:
                        event = cron_job.event
                        server = cron_job.server
                        action = cron_job.action
                        utc_now = datetime.now(pytz.timezone("utc"))
                        cronjob_last_execution_utc = cron_job.last_execution
                        diff = (
                            utc_now - cronjob_last_execution_utc
                            if cronjob_last_execution_utc
                            else None
                        )
                        if (
                            cronjob_last_execution_utc is None
                            or diff.total_seconds() > CRON_THREAD_KILL_TIMEOUT
                        ):
                            cron_job.last_execution = local_date.utcnow()
                            cron_job.save()
                            server.action = action
                            if event is not None:
                                server.event = event
                            server.clean()
                            server.save()
                except:
                    pass

            sleep(CRON_THREAD_KILL_TIMEOUT)

        except KeyboardInterrupt:
            pass