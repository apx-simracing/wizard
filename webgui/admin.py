from django.contrib import admin
from webgui.models import Component, Track, Entry, EntryFile, Event, RaceConditions, Server
from django.utils.html import mark_safe

class ComponentAdmin(admin.ModelAdmin):
    pass
class TrackAdmin(admin.ModelAdmin):
    pass
class EntryAdmin(admin.ModelAdmin): 
    pass
class EntryFileAdmin(admin.ModelAdmin):
    list_display  = ("pk", "file", "entry", 'is_grouped')
    def is_grouped(self, obj):
        component = obj.entry.component if obj.entry else None
        return component is not None and component.component_name in str(obj.file)
    is_grouped.short_description = 'Processed by Wizard'
class EventAdmin(admin.ModelAdmin):
    list_display  = ("name", "json_link")
    def json_link(self, obj):
        return mark_safe("<a target='blank' href='/json/{}/'>JSON</a>".format(obj.pk))
    json_link.allow_tags = True
    json_link.short_description = 'Event configuration'
class RaceConditionsAdmin(admin.ModelAdmin):
    pass
class ServerAdmin(admin.ModelAdmin):
    list_display = ("url", "event", "locked" )
    def get_readonly_fields(self, request, obj):
        if obj and obj.locked:
            return self.readonly_fields + ("event", "packs_path", "build_path", "public_ip", "secret", "url", "status", "locked", "action", )
        return self.readonly_fields + ("status", "locked", )
    pass


admin.site.register(Component, ComponentAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(EntryFile, EntryFileAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(RaceConditions, RaceConditionsAdmin)
admin.site.register(Server, ServerAdmin)

