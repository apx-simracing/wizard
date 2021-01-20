from django.contrib import admin
from webgui.models import (
    Component,
    Track,
    Entry,
    EntryFile,
    Event,
    RaceConditions,
    Server,
    Chat,
)
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django import forms
from django.contrib import admin

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
            user=request.user, type="VEH", do_update=True
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

    list_display = ("name", "url", "event", "locked", "action", "is_running")
    fieldsets = [
        ("APX Settings", {"fields": ["name", "url", "public_ip", "secret", "user"]}),
        (
            "Dedicated server settings",
            {
                "fields": [
                    "event",
                ]
            },
        ),
        (
            "Actions and status",
            {
                "fields": [
                    "action",
                    "locked",
                    "status",
                ]
            },
        ),
        (
            "Keys",
            {
                "fields": [
                    "server_key",
                    "server_unlock_key",
                ]
            },
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
                "server_key",
                "status",
            )
        if self.is_running(obj):
            return self.readonly_fields + (
                "event",
                "server_key",
                "status",
                "locked",
            )
        return self.readonly_fields + ("status", "locked", "is_running", "server_key")

    def is_running(self, obj):
        if not obj or not obj.status:
            return False
        return "not_running" not in obj.status

    is_running.short_description = "Running"


admin.site.register(Component, ComponentAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(EntryFile, EntryFileAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(RaceConditions, RaceConditionsAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(Chat, ChatAdmin)