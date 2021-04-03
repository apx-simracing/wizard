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
)
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django import forms
from django.contrib import admin
from webgui.util import do_component_file_apply
from json import loads

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

    list_display = ("name", "server_name", "track_name", "status_info", "build")
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
                ]
            },
        ),
        (
            "Dedicated server settings",
            {"fields": ["event", "branch"]},
        ),
        (
            "Actions and status",
            {"fields": ["action", "locked", "status_info"]},
        ),
        (
            "Keys",
            {"fields": ["server_key", "server_unlock_key", "log"]},
        ),
    ]

    def get_readonly_fields(self, request, obj):
        if obj and obj.locked:
            return self.readonly_fields + (
                "event",
                "public_ip",
                "secret",
                "url",
                "status",
                "locked",
                "action",
                "status_failures",
                "status_info",
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
            )
        if obj and obj.status_info and "incomp" in obj.status_info:
            self.readonly_fields = self.readonly_fields + (
                "action",
                "branch",
                "event",
                "server_key",
                "server_unlock_key",
                "public_secret",
            )
        return self.readonly_fields + (
            "locked",
            "is_running",
            "status_failures",
            "status_info",
            "public_secret",
        )

    def is_running(self, obj):
        if not obj or not obj.status:
            return False
        return "not_running" not in obj.status

    is_running.short_description = "Running"

    def server_name(self, obj):
        if not obj or not obj.status:
            return "-"
        json = loads(obj.status)
        return json["name"] if "name" in obj.status else "-"

    server_name.short_description = "Server name"

    def track_name(self, obj):
        if not obj or not obj.status:
            return "-"
        json = loads(obj.status)
        return json["track"] if "track" in obj.status else "-"

    track_name.short_description = "Track"


admin.site.register(Component, ComponentAdmin)
admin.site.register(ComponentFile, ComponentFileAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(EntryFile, EntryFileAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(RaceConditions, RaceConditionsAdmin)
admin.site.register(RaceSessions, RaceSessionsAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(Chat, ChatAdmin)
