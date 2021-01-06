from django.contrib import admin
from webgui.models import Component, Track, Entry, Server, RaceConditions
from django.utils.html import mark_safe

class ComponentAdmin(admin.ModelAdmin):
    pass
class TrackAdmin(admin.ModelAdmin):
    pass
class EntryAdmin(admin.ModelAdmin):
    pass
class ServerAdmin(admin.ModelAdmin):
    list_display  = ("name", "json_link")
    def json_link(self, obj):
        return mark_safe("<a target='blank' href='/json/{}/'>JSON</a>".format(obj.pk))
    json_link.allow_tags = True
    json_link.short_description = 'Event configuration'
class RaceConditionsAdmin(admin.ModelAdmin):
    pass

admin.site.register(Component, ComponentAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(RaceConditions, RaceConditionsAdmin)
