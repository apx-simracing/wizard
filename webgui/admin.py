from django.contrib import admin
from webgui.models import Component, Track, Entry, Server, RaceConditions

class ComponentAdmin(admin.ModelAdmin):
    pass
class TrackAdmin(admin.ModelAdmin):
    pass
class EntryAdmin(admin.ModelAdmin):
    pass
class ServerAdmin(admin.ModelAdmin):
    pass
class RaceConditionsAdmin(admin.ModelAdmin):
    pass

admin.site.register(Component, ComponentAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(RaceConditions, RaceConditionsAdmin)
