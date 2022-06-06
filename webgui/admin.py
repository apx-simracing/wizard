from django.contrib import admin
from django.core import management
from django.shortcuts import redirect
from webgui.models import (
    Component,
    Track,
    Entry,
    EntryFile,
    Event,
    RaceConditions,
    Server,
    RaceSessions,
    ServerCron,
    ServerFile,
    TrackFile,
    background_action_server,
)
from wizard.settings import RECIEVER_PORT_RANGE, EASY_MODE
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.contrib import admin
from webgui.util import (
    get_random_string,
    get_secret,
    get_free_tcp_port,
    bootstrap_reciever,
)
from os import mkdir
from os.path import join
from wizard.settings import BASE_DIR
from django.urls import path
from django.http import HttpResponseRedirect
from pydng import generate_name
from django.forms.widgets import CheckboxSelectMultiple
from threading import Thread

admin.site.site_url = None
admin.site.site_title = "APX"


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    ordering = ["component_name"]

    def get_fieldsets(self, request, obj):
        fieldsets = (
            (
                "Mod properties",
                {
                    "fields": (
                        "type",
                        "steam_id",
                        "base_component",
                        "alternative_name",
                        "component_name",
                        "short_name",
                        "is_official",
                    ),
                },
            ),
            (
                "Update settings",
                {
                    "fields": (
                        "update",
                        "component_files",
                        "numberplate_template_l",
                        "numberplate_template_mask_l",
                        "numberplate_template_r",
                        "numberplate_template_mask_r",
                        "mask_positions",
                        "template",
                    ),
                },
            ),
            (
                "Warnings",
                {
                    "fields": ("ignore_warnings",),
                },
            ),
        )
        if EASY_MODE:
            fieldsets[0][1]["fields"] = (
                "type",
                "steam_id",
                "component_name",
                "is_official",
            )
            fieldsets[1][1]["fields"] = (
                "update",
                "template",
            )
        return fieldsets


from django.contrib.admin.views.main import ChangeList


class TrackChangelist(ChangeList):
    def get_results(self, request):
        super(TrackChangelist, self).get_results(request)
        totals = self.result_list
        self.fack = "fasf"
        print(totals)


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    ordering = ["layout", "component__component_name"]
    list_display = (
        "layout",
        "component",
    )
    """
    change_list_template = "admin/track_list.html"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        all_tracks = Track.objects.all().order_by("component__component_name", "layout")
        result = {}
        for track in all_tracks:
            component = track.component
            if component not in result:
                result[component] = []
            result[component].append(track)
        response.context_data["tracks"] = result
        return response
    """

    def get_form(self, request, obj=None, **kwargs):
        form = super(TrackAdmin, self).get_form(request, obj=None, **kwargs)
        if not EASY_MODE:
            form.base_fields["component"].queryset = Component.objects.filter(
                type="LOC"
            )
        return form

    def get_fieldsets(self, request, obj):
        fieldsets = (
            (
                "Track",
                {
                    "fields": ("component",),
                },
            ),
            (
                "Layout",
                {
                    "fields": ("layout",),
                },
            ),
        )
        if EASY_MODE:
            fieldsets = (
                (
                    "Layout",
                    {
                        "fields": ("layout",),
                    },
                ),
            )

        return fieldsets


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    ordering = ("component__component_name",)

    change_list_template = "admin/entry_list.html"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        all_entries = Entry.objects.all().order_by("component__component_name")
        result = {}
        for entry in all_entries:
            component = entry.component
            if component not in result:
                result[component] = []
            files = EntryFile.objects.filter(entry=entry)
            result[component].append({"entry": entry, "files": files})
        response.context_data["entries"] = result
        return response

    def get_form(self, request, obj=None, **kwargs):
        form = super(EntryAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["component"].queryset = Component.objects.filter(type="VEH")
        return form

    def get_fieldsets(self, request, obj):
        fieldsets = (
            (
                "Vehicle",
                {
                    "fields": ("component",),
                },
            ),
            (
                "Team",
                {
                    "fields": (
                        "team_name",
                        "vehicle_number",
                        "base_class",
                        "token",
                        "pit_group",
                        "additional_overwrites",
                    ),
                },
            ),
        )
        if EASY_MODE:
            fieldsets[1][1]["fields"] = ("team_name", "vehicle_number", "base_class")
        return fieldsets

@admin.register(ServerCron)
class ServerCronAdmin(admin.ModelAdmin):
    ordering = ("server", "disabled", "start_time")
    actions = ["disable", "enable", "execute", "update"]

    def disable(self, request, queryset):
        for element in queryset:
            element.disabled = True
            element.save()

    disable.short_description = "Disable selected server schedules"

    def update(self, request, queryset):
        for element in queryset:
            element.save()

    update.short_description = "Recreate selected schedules in Windows task planning"

    def enable(self, request, queryset):
        for element in queryset:
            element.disabled = False
            element.save()

    enable.short_description = "Enable selected server schedules"

    def execute(self, request, queryset):
        for element in queryset:
            management.call_command("cron_run", element.pk)

    execute.short_description = "Execute selected server schedule action ONCE"

    def get_readonly_fields(self, request, obj):
        return self.readonly_fields


@admin.register(EntryFile)
class EntryFileAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):

        entry = request.GET.get("entry")
        form = super(EntryFileAdmin, self).get_form(request, obj=None, **kwargs)
        if entry is not None:
            form.base_fields["entry"].initial = int(entry)
        return form

    def response_delete(self, request, obj_display, obj_id):
        return redirect("/admin/webgui/entry")

    def response_add(self, request, obj, post_url_continue=None):
        return redirect("/admin/webgui/entry")

    def response_change(self, request, obj):
        return redirect("/admin/webgui/entry")

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

    def get_fieldsets(self, request, obj):
        fieldsets = (
            (
                "Vehicle",
                {
                    "fields": ("entry",),
                },
            ),
            (
                "File",
                {
                    "fields": (
                        "file",
                        "mask_added",
                    ),
                },
            ),
        )
        if EASY_MODE:
            fieldsets[1][1]["fields"] = ("file",)
        return fieldsets


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    ordering = ["name"]
    actions = ["copy"]
    """
    change_form_template = (
        "admin/event_change_form.html"
    )
    change_list_template = (
        "admin/event_list.html"
    )
    """
    filter_horizontal = (
        "tracks",
        "entries",
        "signup_components",
        "files",
    )

    def copy(self, request, queryset):
        for element in queryset:
            element.pk = None
            element.name = element.name + " Copy"
            element.save()
        pass

    copy.short_description = "Copy event"

    def get_form(self, request, obj=None, **kwargs):
        form = super(EventAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["entries"].queryset = Entry.objects.filter(
            component__type="VEH"
        ).order_by("team_name")
        form.base_fields["signup_components"].queryset = Component.objects.filter(
            type="VEH"
        ).order_by("component_name")
        return form

    def all_clients(self, obj):
        if not obj:
            return "0/0"
        return "{}/{}".format(obj.clients, obj.ai_clients)

    all_clients.short_description = "#/AI"

    def all_aids(self, obj):
        if not obj:
            return "-"
        return "{}/{}/{}/{}/{}".format(
            obj.allow_auto_clutch,
            obj.allow_ai_toggle,
            obj.allow_traction_control,
            obj.allow_anti_lock_brakes,
            obj.allow_stability_control,
        )

    all_aids.short_description = "Auto clutch/ AI toggle/ TC/ ABS/ SC"

    list_display = (
        "name",
        "damage",
        "all_clients",
        "all_aids",
        "rejoin",
        "real_name",
        "replays",
        "real_weather",
        "temp_offset",
        "weather_api",
        "weather_key",
    )

    fieldsets = (
        (
            "Event structure",
            {
                "fields": (
                    "name",
                    "mod_name",
                    "mod_version",
                    "event_mod_version",
                    "entries",
                    "tracks",
                    "signup_components",
                    "include_stock_skins",
                ),
            },
        ),
        (
            "Session join options",
            {
                "fields": (
                    "admin_password",
                    "password",
                    "clients",
                    "ai_clients",
                    "ai_strength",
                    "pause_while_zero_players",
                    "qualy_join_mode",
                    "rejoin",
                    "real_name",
                    "deny_votings",
                    "welcome_message",
                ),
            },
        ),
        (
            "Driving aids",
            {
                "fields": (
                    "allow_traction_control",
                    "allow_anti_lock_brakes",
                    "allow_stability_control",
                    "allow_auto_shifting",
                    "allow_steering_help",
                    "allow_braking_help",
                    "allow_auto_clutch",
                    "allow_invulnerability",
                    "allow_auto_pit_stop",
                    "allow_opposite_lock",
                    "allow_spin_recovery",
                    "allow_ai_toggle",
                    "forced_driving_view",
                ),
            },
        ),
        (
            "Network and connectivity settings",
            {
                "fields": (
                    "downstream",
                    "upstream",
                    "collision_fade_threshold",
                    "enable_auto_downloads",
                    "files",
                    "force_versions",
                ),
            },
        ),
        (
            "Simulator multipliers",
            {
                "fields": (
                    "fuel_multiplier",
                    "race_multiplier",
                    "tire_multiplier",
                    "damage",
                )
            },
        ),
        (
            "Session settings",
            {
                "fields": (
                    "qualy_mode",
                    "after_race_delay",
                    "delay_between_sessions",
                    "conditions",
                    "skip_all_session_unless_configured",
                    "replays",  # weather is disabled atm
                    "reconaissance_laps",
                    "start_type",
                    "must_be_stopped",
                    "pit_speed_override",
                ),
            },
        ),
        (
            "Weather",
            {
                "fields": ("real_weather", "weather_api", "weather_key", "temp_offset"),
            },
        ),
        (
            "Penalties",
            {
                "fields": (
                    "cuts_allowed",
                    "rules",
                    "blue_flag_mode",
                )
            },
        ),
        (
            "Parc Ferme",
            {
                "fields": (
                    "parc_ferme",
                    "free_settings",
                    "fixed_setups",
                )
            },
        ),
    )


@admin.register(RaceSessions)
class RaceSessionsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Session",
            {
                "fields": (
                    "description",
                    "type",
                ),
            },
        ),
        (
            "Length",
            {
                "fields": (
                    "start",
                    "laps",
                    "length",
                    "race_finish_criteria",
                ),
            },
        ),
        (
            "Grip",
            {
                "fields": (
                    "real_road_time_scale",
                    "grip",
                    "grip_needle",
                ),
            },
        ),
    )


@admin.register(RaceConditions)
class RaceConditionsAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(RaceConditionsAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["sessions"].widget = CheckboxSelectMultiple()
        return form


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    ordering = ["name"]
    change_list_template = (
        "admin/server_list.html" if not EASY_MODE else "admin/server_list_easy.html"
    )
    actions = [
        # "get_thumbnails", this is disabled  until work on the timing resumes.
        "apply_reciever_update",
        "delete_chats_and_messages",
        "start_server",
        "stop_server",
        "update_server_content",
        "update_server_only",
    ]

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

        server_children = join(root, "server_children")
        if not exists(server_children):
            mkdir(server_children)

        local_path = generate_name()
        secret = get_secret(20)
        servers = Server.objects.all()
        taken_ports = []
        for server in servers:
            url = server.url
            if "localhost" in url:
                # it's on the same box
                port = url.replace("http://localhost:", "").replace("/", "")
                taken_ports.append(int(port))
        port = get_free_tcp_port(
            5, RECIEVER_PORT_RANGE[0], taken_ports, RECIEVER_PORT_RANGE[1]
        )
        if port in taken_ports:
            self.message_user(
                request, "We could not get a free port", level=messages.ERROR
            )
            return HttpResponseRedirect("../")

        server_path = join(server_children, local_path)
        if not exists(server_path):
            mkdir(server_path)
            new_server = Server()
            new_server.local_path = local_path
            new_server.secret = secret
            new_server.url = "http://localhost:{}/".format(port)
            new_server.name = local_path
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

    def start_server(self, request, queryset):
        for server in queryset:
            server.action = "S+"
            server.save()
            background_thread = Thread(
                target=background_action_server, args=(server,), daemon=True
            )
            background_thread.start()
            messages.success(request, f"Requested start for {server}")

    start_server.short_description = "Start selected servers"

    def update_server_content(self, request, queryset):
        for server in queryset:
            server.action = "D+F"
            server.save()
            background_thread = Thread(
                target=background_action_server, args=(server,), daemon=True
            )
            background_thread.start()
            messages.success(request, f"Requested update for {server}")

    update_server_content.short_description = "Update server content"

    def update_server_only(self, request, queryset):
        for server in queryset:
            server.action = "U"
            server.save()
            background_thread = Thread(
                target=background_action_server, args=(server,), daemon=True
            )
            background_thread.start()
            messages.success(request, f"Requested update for {server}")

    update_server_only.short_description = "Update to latest version of Steam branch"

    def stop_server(self, request, queryset):
        for server in queryset:
            server.action = "R-"
            server.save()
            background_thread = Thread(
                target=background_action_server, args=(server,), daemon=True
            )
            background_thread.start()
            messages.success(request, f"Requested stop for {server}")

    stop_server.short_description = "Stop selected servers"

    def apply_reciever_update(self, request, queryset):
        for server in queryset:
            if server.is_created_by_apx:
                if "Server is running" in server.status_info:
                    messages.error(
                        request,
                        "The server {} is running. Stop it first.".format(server.name),
                    )
                else:
                    path = join(
                        BASE_DIR, "server_children", server.local_path, "update.lock"
                    )
                    with open(path, "w") as file:
                        file.write("update")
                    server.state = "Waiting for reciever update"
                    server.save()
                    messages.success(
                        request,
                        "Reciever of server {} marked for update.".format(server.name),
                    )
            else:
                messages.warning(
                    request,
                    "The server {} is not created by APX, so you have to update the reciever by yourself.".format(
                        server.name
                    ),
                )

    list_display = (
        "name",
        "event",
        "status_info",
        "is_created_by_apx",
        "ports",
    )

    def get_fieldsets(self, request, obj):
        fieldsets = [
            (
                "APX Settings",
                {
                    "fields": [
                        "name",
                        "url",
                        "discord_url",
                        "ignore_start_hook",
                        "ignore_stop_hook",
                        "ignore_updates_hook",
                        "secret",
                        "local_path",
                        "session_id",
                        "sim_port",
                        "http_port",
                        "webui_port",
                        "steamcmd_bandwidth",
                        "remove_unused_mods",
                        "heartbeat_only",
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
                        "is_created_by_apx",
                        "update_on_build",
                        "remove_cbash_shaders",
                        "remove_settings",
                        "collect_results_replays",
                    ]
                },
            ),
            (
                "Chatting and commands",
                {
                    "fields": [
                        "message"
                    ]
                },
            ),
            (
                "Keys",
                {"fields": ["server_key", "server_unlock_key", "logfile"]},
            ),
        ]
        if obj.is_created_by_apx:
            fieldsets[0][1]["fields"] = [
                "name",
                "secret",
                "url",
                "local_path",
                "session_id",
                "sim_port",
                "http_port",
                "webui_port",
                "steamcmd_bandwidth",
                "remove_unused_mods",
            ]
        if EASY_MODE:
            fieldsets[0][1]["fields"].remove("remove_unused_mods")
            fieldsets[0][1]["fields"].remove("steamcmd_bandwidth")
            fieldsets[0][1]["fields"].remove("session_id")
            fieldsets[0][1]["fields"].remove("local_path")
            fieldsets[0][1]["fields"].remove("webui_port")
            if "heartbeat_only" in fieldsets[0][1]["fields"]:
                fieldsets[0][1]["fields"].remove("heartbeat_only")
            fieldsets[2][1]["fields"] = [
                "action",
                "status_info",
                "is_created_by_apx",
                "update_on_build",
                "collect_results_replays",
            ]
        return fieldsets

    def get_readonly_fields(self, request, obj):
        if self.is_running(obj):
            return self.readonly_fields + (
                "event",
                "status_info",
                "is_created_by_apx",
                "state",
                "logfile",
            )
        return self.readonly_fields + (
            "is_running",
            "status_info",
            "is_created_by_apx",
            "state",
            "local_path",
            "logfile",
        )

    def is_running(self, obj):
        if not obj:
            return False
        status = self.get_status(obj)
        if not status or status == "-":
            return False
        return (
            "Server is running" not in status
        )  # get_stauts returns the display text, not the status anymore.

    is_running.short_description = "Running"

    def get_status(self, obj):
        return obj.status_info

@admin.register(ServerFile)
class ServerFileAdmin(admin.ModelAdmin):
    pass


@admin.register(TrackFile)
class TrackFileAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(TrackFileAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields["track"].queryset = Track.objects.filter(component__type="LOC")
        return form


admin.site.unregister(Group)
admin.site.unregister(User)

if EASY_MODE:
    admin.site.unregister(Component)