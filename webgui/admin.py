from django.contrib import admin
from webgui.models import (
    Component,
    Track,
    Entry,
    EntryFile,
    ComponentFile,
    Event,
    RaceConditions,
    Server,
    Chat,
    RaceSessions,
    ServerCron,
    TickerMessage,
    ServerPlugin,
    TrackFile,
)
from wizard.settings import OPENWEATHERAPI_KEY
from django.contrib import messages
from django.utils.html import mark_safe
from django.contrib.auth.models import Group
from django import forms
from django.contrib import admin
from webgui.util import (
    do_component_file_apply,
    get_server_hash,
    run_apx_command,
    get_random_string,
    get_secret,
    RECIEVER_DOWNLOAD_FROM,
    get_free_tcp_port,
    bootstrap_reciever,
)
from json import loads
from datetime import datetime, timedelta
import pytz
import tarfile
from os import unlink, mkdir, linesep
from os.path import join, exists
from wizard.settings import MEDIA_ROOT, BASE_DIR
from math import floor
from django.urls import path
from django.http import HttpResponseRedirect

admin.site.site_url = None
admin.site.site_title = "APX"


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    pass


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(TrackAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["component"].queryset = Component.objects.filter(type="LOC")
        return form


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(EntryAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["component"].queryset = Component.objects.filter(type="VEH")
        return form


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    readonly_fields = ("success", "date")
    list_display = (
        "server",
        "message",
        "success",
        "date",
    )


@admin.register(ComponentFile)
class ComponentFileAdmin(admin.ModelAdmin):
    pass


@admin.register(ServerCron)
class ServerCronAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj):
        return self.readonly_fields + ("last_execution",)


@admin.register(EntryFile)
class EntryFileAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(EntryFileAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["entry"].queryset = Entry.objects.filter(
            component__do_update=True
        )
        return form

    list_display = (
        "computed_name",
        "mask_added",
        "is_grouped",
    )

    def computed_name(self, obj):
        return str(obj.entry) + ": " + str(obj.file)

    def is_grouped(self, obj):
        component = obj.entry.component if obj.entry else None
        return component is not None and component.component_name in str(obj.file)

    is_grouped.short_description = "Processed by Wizard"
    computed_name.short_description = "Vehicle and filename"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(EventAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["entries"].queryset = Entry.objects.filter(
            component__type="VEH"
        )
        form.base_fields["tracks"].queryset = Track.objects.filter(
            component__type="LOC"
        )
        form.base_fields["signup_components"].queryset = Component.objects.filter(
            type="VEH"
        )
        return form

    def all_clients(self, obj):
        if not obj:
            return "0/0"
        return "{}/{}".format(obj.clients, obj.ai_clients)

    all_clients.short_description = "#/AI"

    list_display = (
        "name",
        "damage",
        "all_clients",
        "rejoin",
        "allow_auto_clutch",
        "allow_ai_toggle",
        "allow_traction_control",
        "allow_anti_lock_brakes",
        "allow_stability_control",
        "real_name",
        "replays",
    )


@admin.register(RaceSessions)
class RaceSessionsAdmin(admin.ModelAdmin):
    pass


@admin.register(RaceConditions)
class RaceConditionsAdmin(admin.ModelAdmin):
    pass


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    change_list_template = "admin/server_list.html"
    actions = ["reset_status", "get_thumbnails"]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("wizard/", self.run_wizard),
        ]
        return my_urls + urls

    def run_wizard(self, request):
        root = BASE_DIR
        from os.path import exists, join
        from json import dumps
        from threading import Thread

        server_children = join(root, "server_children")
        if not exists(server_children):
            mkdir(server_children)

        public_secret = get_random_string(20)
        secret = get_secret(20)
        servers = Server.objects.all()
        taken_ports = []
        for server in servers:
            url = server.url
            if "localhost" in url:
                # it's on the same box
                port = url.replace("http://localhost:", "").replace("/", "")
                taken_ports.append(int(port))
        port = get_free_tcp_port(5, 8080, taken_ports)
        if port in taken_ports:
            self.message_user(
                request, "We could not get a free port", level=messages.ERROR
            )
            return HttpResponseRedirect("../")

        server_path = join(server_children, public_secret)
        if not exists(server_path):
            mkdir(server_path)
            new_server = Server()
            new_server.public_secret = public_secret
            new_server.secret = secret
            new_server.url = "http://localhost:{}/".format(port)
            new_server.name = "New APX server"
            new_server.state = "Created server element"
            new_server.save()

            background_thread = Thread(
                target=bootstrap_reciever,
                args=(server_path, new_server, port, secret),
                daemon=True,
            )
            background_thread.start()

        else:
            self.message_user(
                request, "The server is already existing", level=messages.WARNING
            )
        return HttpResponseRedirect("../")

    def reset_status(self, request, queryset):
        for server in queryset:
            server.status = None
            server.save()
        messages.success(request, "Status are resetted.")

    reset_status.short_description = "Reset status (if stuck)"

    def get_thumbnails(self, request, queryset):
        try:
            for server in queryset:

                url = server.url
                key = get_server_hash(url)
                media_thumbs_root = join(MEDIA_ROOT, "thumbs")
                if not exists(media_thumbs_root):
                    mkdir(media_thumbs_root)

                server_thumbs_path = join(media_thumbs_root, key)
                if not exists(server_thumbs_path):
                    mkdir(server_thumbs_path)

                # server may changed -> download thumbs
                thumbs_command = run_apx_command(
                    key,
                    "--cmd thumbnails --args {}".format(
                        join(server_thumbs_path, "thumbs.tar.gz")
                    ),
                )
                # unpack the livery thumbnails, if needed
                if not exists(join(MEDIA_ROOT, "thumbs")):
                    mkdir(join(MEDIA_ROOT, "thumbs"))
                server_key_path = join(MEDIA_ROOT, "thumbs", key)
                if not exists(server_key_path):
                    mkdir(server_key_path)

                server_pack_path = join(server_key_path, "thumbs.tar.gz")
                if exists(server_pack_path):
                    # unpack liveries
                    file = tarfile.open(server_pack_path)
                    file.extractall(path=server_key_path)
                    file.close()
                    unlink(server_pack_path)
            messages.success(request, "The thumbnails are saved")
        except Exception as e:
            messages.error(request, e)

    get_thumbnails.short_description = "Get thumbnails"

    list_display = (
        "name",
        "event",
        "state",
        "status_info",
        "is_created_by_apx",
        "ports",
    )
    fieldsets = [
        (
            "APX Settings",
            {
                "fields": [
                    "name",
                    "url",
                    "secret",
                    "public_secret",
                    "session_id",
                    "sim_port",
                    "http_port",
                    "webui_port",
                    "steamcmd_bandwith",
                ]
            },
        ),
        (
            "Dedicated server settings",
            {"fields": ["event", "branch"]},
        ),
        (
            "Actions and status",
            {
                "fields": [
                    "action",
                    "status_info",
                    "state",
                    "is_created_by_apx",
                    "update_on_build",
                    "update_weather_on_start",
                ]
            },
        ),
        (
            "Keys",
            {"fields": ["server_key", "server_unlock_key", "logfile"]},
        ),
    ]

    def get_readonly_fields(self, request, obj):
        if self.is_running(obj):
            return self.readonly_fields + (
                "event",
                "status_info",
                "is_created_by_apx",
                "state",
                "public_secret",
                "logfile",
            )
        return self.readonly_fields + (
            "is_running",
            "status_info",
            "is_created_by_apx",
            "state",
            "public_secret",
            "logfile",
        )

    def is_running(self, obj):
        if not obj:
            return False
        status = self.get_status(obj)
        if not status:
            return False
        return "not_running" not in status

    is_running.short_description = "Running"

    def get_status(self, obj):
        return obj.status


@admin.register(TickerMessage)
class TickerMessageAdmin(admin.ModelAdmin):
    list_display = ["date", "type", "session_id", "event_time", "session", "__str__"]


@admin.register(ServerPlugin)
class ServerPluginAdmin(admin.ModelAdmin):
    pass


@admin.register(TrackFile)
class TrackFileAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(TrackFileAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["track"].queryset = Component.objects.filter(type="LOC")
        return form