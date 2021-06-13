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
    ServerStatustext,
    ServerCron,
    TickerMessage,
    ServerPlugin,
    TrackFile,
)
from wizard.settings import OPENWEATHERAPI_KEY
from django.contrib import messages
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django import forms
from django.contrib import admin
from webgui.util import do_component_file_apply, get_server_hash, run_apx_command
from json import loads
from datetime import datetime, timedelta
import pytz
import tarfile
from os import unlink, mkdir, linesep
from os.path import join, exists
from wizard.settings import MEDIA_ROOT
from math import floor

admin.site.site_url = None
admin.site.site_title = "APX"


class ComponentAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ComponentAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(ComponentAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Component.objects.filter(user=request.user)
        else:
            return Component.objects.all()


class TrackAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(TrackAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["component"].queryset = Component.objects.filter(
            user=request.user, type="LOC"
        )
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(TrackAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Track.objects.filter(user=request.user)
        else:
            return Track.objects.all()


class EntryAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(EntryAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["component"].queryset = Component.objects.filter(
            user=request.user, type="VEH"
        )
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(EntryAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Entry.objects.filter(user=request.user)
        else:
            return Entry.objects.all()


class ChatAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ChatAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["server"].queryset = Server.objects.filter(user=request.user)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(ChatAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Chat.objects.filter(user=request.user)
        else:
            return Chat.objects.all()

    readonly_fields = ("success", "date")
    list_display = (
        "server",
        "message",
        "success",
        "date",
    )


class ComponentFileAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ComponentFileAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(ComponentFileAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return ComponentFile.objects.filter(user=request.user)
        else:
            return ComponentFile.objects.all()


class ServerCronAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ServerCronAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(ServerCronAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return ServerCron.objects.filter(user=request.user)
        else:
            return ServerCron.objects.all()

    def get_readonly_fields(self, request, obj):
        return self.readonly_fields + ("last_execution",)


class EntryFileAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(EntryFileAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["entry"].queryset = Entry.objects.filter(
            user=request.user, component__do_update=True
        )
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(EntryFileAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return EntryFile.objects.filter(user=request.user)
        else:
            return EntryFile.objects.all()

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


class EventAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(EventAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["entries"].queryset = Entry.objects.filter(
            user=request.user, component__type="VEH"
        )
        form.base_fields["tracks"].queryset = Track.objects.filter(
            user=request.user, component__type="LOC"
        )
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        form.base_fields["conditions"].queryset = RaceConditions.objects.filter(
            user=request.user
        )
        form.base_fields["signup_components"].queryset = Component.objects.filter(
            user=request.user, type="VEH"
        )
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(EventAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Event.objects.filter(user=request.user)
        else:
            return Event.objects.all()

    list_display = ("name", "json_link")

    def json_link(self, obj):
        return mark_safe("<a target='blank' href='/json/{}/'>JSON</a>".format(obj.pk))

    json_link.allow_tags = True
    json_link.short_description = "Event configuration"


class RaceSessionsAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(RaceSessionsAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(RaceSessionsAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return RaceSessions.objects.filter(user=request.user)
        else:
            return RaceSessions.objects.all()


class RaceConditionsAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(RaceConditionsAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(RaceConditionsAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return RaceConditions.objects.filter(user=request.user)
        else:
            return RaceConditions.objects.all()


class ServerAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ServerAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["event"].queryset = Event.objects.filter(user=request.user)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(ServerAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Server.objects.filter(user=request.user)
        else:
            return Server.objects.all()

    actions = ["reset_status", "force_unlock", "get_thumbnails"]

    def reset_status(self, request, queryset):
        for server in queryset:
            text = ServerStatustext()
            text.status = None
            text.user = request.user
            text.server = server
            text.save()
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

    def force_unlock(self, request, queryset):
        queryset.update(locked=False)
        messages.success(request, "Server unlocked")

    force_unlock.short_description = "Unlock (if stuck)"

    list_display = ("name", "server_name", "track_name", "status_info")
    fieldsets = [
        (
            "APX Settings",
            {
                "fields": [
                    "name",
                    "url",
                    "public_ip",
                    "secret",
                    "public_secret",
                    "user",
                    "status_failures",
                    "session_id",
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
                    "locked",
                    "status_info",
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
        if obj and obj.locked:
            return self.readonly_fields + (
                "event",
                "public_ip",
                "secret",
                "url",
                "locked",
                "action",
                "status_failures",
                "status_info",
                "logfile",
                "server_key",
                "server_unlock_key",
                "public_secret",
            )
        if self.is_running(obj):
            return self.readonly_fields + (
                "event",
                "locked",
                "status_failures",
                "status_info",
                "public_secret",
                "logfile",
            )
        return self.readonly_fields + (
            "locked",
            "is_running",
            "status_failures",
            "status_info",
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
        status = None
        try:
            status = ServerStatustext.objects.filter(server=self.pk).first().status
        except:
            pass
        return status

    def server_name(self, obj):
        status = self.get_status(obj)
        if not obj or not status:
            return "-"
        json = loads(status)
        return json["name"] if "name" in json else "-"

    server_name.short_description = "Server name"

    def track_name(self, obj):
        status = self.get_status(obj)
        if not obj or not status:
            return "-"
        json = loads(status)
        return json["track"] if "track" in status else "-"

    track_name.short_description = "Track"


class ServerStatustextAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ServerStatustextAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(ServerStatustextAdmin, self).get_changeform_initial_data(
            request
        )
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return []
        else:
            return ServerStatustext.objects.all()

    list_display = ["server", "session_id", "__str__"]


class TickerMessageAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(TickerMessageAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(TickerMessageAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return TickerMessage.objects.filter(user=request.user)
        else:
            return TickerMessage.objects.all()

    list_display = ["date", "type", "session_id", "event_time", "session", "__str__"]


class ServerPluginAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ServerPluginAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(ServerPluginAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return ServerPlugin.objects.filter(user=request.user)
        else:
            return ServerPlugin.objects.all()


class TrackFileAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(TrackFileAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["user"].queryset = User.objects.filter(pk=request.user.pk)
        form.base_fields["track"].queryset = Component.objects.filter(
            user=request.user, type="LOC"
        )
        return form

    def get_changeform_initial_data(self, request):
        get_data = super(TrackFileAdmin, self).get_changeform_initial_data(request)
        get_data["user"] = request.user.pk
        return get_data

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return TrackFile.objects.filter(user=request.user)
        else:
            return TrackFile.objects.all()


admin.site.register(TrackFile, TrackFileAdmin)
admin.site.register(TickerMessage, TickerMessageAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(ComponentFile, ComponentFileAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(EntryFile, EntryFileAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(RaceConditions, RaceConditionsAdmin)
admin.site.register(RaceSessions, RaceSessionsAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(ServerStatustext, ServerStatustextAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(ServerCron, ServerCronAdmin)
admin.site.register(ServerPlugin, ServerPluginAdmin)
