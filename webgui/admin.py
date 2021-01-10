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

admin.site.unregister(User)
admin.site.unregister(Group)


class ComponentAdmin(admin.ModelAdmin):
    pass


class TrackAdmin(admin.ModelAdmin):
    pass


class EntryAdmin(admin.ModelAdmin):
    pass


class ChatAdmin(admin.ModelAdmin):
    readonly_fields = ("success", "date")
    list_display = (
        "server",
        "message",
        "success",
        "date",
    )


class EntryFileAdmin(admin.ModelAdmin):
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
    list_display = ("name", "json_link")

    def json_link(self, obj):
        return mark_safe("<a target='blank' href='/json/{}/'>JSON</a>".format(obj.pk))

    json_link.allow_tags = True
    json_link.short_description = "Event configuration"


class RaceConditionsAdmin(admin.ModelAdmin):
    pass


class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "event", "locked", "action", "is_running")
    fieldsets = [
        ("APX Settings", {"fields": ["name", "url", "public_ip", "secret"]}),
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
            )
        if self.is_running(obj):
            return self.readonly_fields + ("event",)
        return self.readonly_fields + ("status", "locked", "is_running")

    def is_running(self, obj):
        if not obj:
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