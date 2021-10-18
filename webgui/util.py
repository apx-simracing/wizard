from wizard.settings import (
    APX_ROOT,
    MEDIA_ROOT,
    PACKS_ROOT,
    DISCORD_WEBHOOK,
    DISCORD_WEBHOOK_NAME,
    DISCORD_RACE_CONTROL_WEBHOOK,
    DISCORD_RACE_CONTROL_WEBHOOK_NAME,
    OPENWEATHERAPI_KEY,
    BASE_DIR,
    PUBLIC_URL,
    BASE_DIR,
    MAX_STEAMCMD_BANDWIDTH,
    WEBUI_PORT_RANGE,
    HTTP_PORT_RANGE,
    SIM_PORT_RANGE,
    MSG_LOGO,
    USE_GLOBAL_STEAMCMD,
)
import hashlib
import subprocess
from urllib.parse import urlparse
from re import match
from django.dispatch import receiver
from os.path import join, exists, basename
from os import mkdir, listdir, unlink, linesep
from shutil import copyfile
from . import models
from json import loads, dumps
import random
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
import socket
import discord
from requests import post, get
import secrets
import string
import socket
import random
import logging
import zipfile, io
from time import sleep
from collections import OrderedDict

logger = logging.getLogger(__name__)

FILE_NAME_SUFFIXES = [
    ".json",
    "EXTRA4.dds",
    "EXTRA5.dds",
    "EXTRA6.dds",
    "Window.dds",
    "region.dds",
    "windshieldout.dds",
    "WINDSHIELDIN.dds",
    "WINDOWSIN.dds",
    "WINDOWSOUT.dds",
    "WINDOW.dds",
    "_Region.dds",
    "helmet.dds",
    "icon.png",
    "SMicon.dds",
    "icon.dds",
    "helmet.png",
    "-icon-128x72.png",
    "-icon-256x144.png",
    "-icon-512x288.png",
    "-icon-1024x576.png",
    "-icon-2048x1152.png",
    ".dds",
]

FILE_NAME_SUFFIXES_MEANINGS = [
    "JSON file",
    "EXTRA4",
    "EXTRA5",
    "EXTRA6",
    "Window file",
    "Region file",
    "Outer windshield file",
    "Inner windshield file",
    "Inner windows file",
    "Outer windows file",
    "Windscreen file",
    "Livery region",
    "Helmet livery",
    "Icon",
    "SMIcon",
    "Icon (DDS)",
    "Helmet livery (PNG)",
    "Icon 128x72",
    "Icon 256x144",
    "Icon 512x288",
    "Icon 1024x576",
    "Icon 2048x1152",
    "Livery main file",
]

RECIEVER_COMP_INFO = open(join(BASE_DIR, "release")).read()
RECIEVER_DOWNLOAD_FROM = "https://github.com/apx-simracing/reciever/releases/download/R83/reciever-2021R83.zip"


def get_update_filename(instance, filename):
    component_name = instance.component_name
    full_user_path = join(MEDIA_ROOT)
    if not exists(full_user_path):
        mkdir(full_user_path)

    liveries_path = join(full_user_path, "liveries")
    if not exists(liveries_path):
        mkdir(liveries_path)

    component_path = join(liveries_path, component_name)
    if not exists(component_path):
        mkdir(component_path)

    return join("liveries", component_name, filename)


def get_livery_mask_root(instance, filename):
    root_path = join(MEDIA_ROOT, "templates")
    if not exists(root_path):
        mkdir(root_path)
    return join("templates", filename)


def get_component_file_root(instance, filename):
    root_path = join(MEDIA_ROOT, "templates")
    if not exists(root_path):
        mkdir(root_path)
    return join("templates", filename)


def get_conditions_file_root(instance, filename):
    full_path = join(MEDIA_ROOT)
    if not exists(full_path):
        mkdir(full_path)
    conditions_path = join(full_path, "conditions")
    if not exists(conditions_path):
        mkdir(conditions_path)
    return join("conditions", filename)


def track_filename(instance, filename):
    component_short_name = instance.track.component.short_name
    component_name = instance.track.component.component_name
    path = join(MEDIA_ROOT, "tracks", component_name)

    file_path = join(path, filename)
    return file_path


def livery_filename(instance, filename):
    vehicle_number = instance.entry.vehicle_number
    component_short_name = instance.entry.component.short_name
    component_name = instance.entry.component.component_name
    full_user_path = join(MEDIA_ROOT)
    if not exists(full_user_path):
        mkdir(full_user_path)

    liveries_path = join(full_user_path, "liveries")
    if not exists(liveries_path):
        mkdir(liveries_path)

    component_path = join(liveries_path, component_name)
    if not exists(component_path):
        mkdir(component_path)

    selected_suffix = None
    for suffix in FILE_NAME_SUFFIXES:
        if str(filename).endswith(suffix):
            selected_suffix = suffix
    if selected_suffix is None:
        raise ValidationError("We can't identify that file purpose")
    new_file_path = join(
        "liveries",
        component_name,
        "{}_{}{}".format(component_short_name, vehicle_number, selected_suffix),
    )
    return new_file_path


def get_key_root_path(instance, filename):
    hash_code = get_server_hash(instance.url)
    full_path = join(MEDIA_ROOT, "keys", hash_code)
    if not exists(full_path):
        mkdir(full_path)
    return join("keys", hash_code, filename)


def get_plugin_root_path(instance, filename):
    if not exists(join(join(MEDIA_ROOT, "plugins"))):
        mkdir(join(MEDIA_ROOT, "plugins"))
    full_path = join(MEDIA_ROOT, "plugins")
    if not exists(full_path):
        mkdir(full_path)
    return join("plugins", filename)


def get_logfile_root_path(instance, filename):
    hash_code = get_server_hash(instance.url)
    full_path = join(MEDIA_ROOT, "logs", hash_code)
    if not exists(full_path):
        mkdir(full_path)
    return join("keys", hash_code, filename)


def remove_orphan_files():
    root_path = join(MEDIA_ROOT, "liveries")
    files = models.EntryFile.objects.all()
    components = {}
    for file in files:
        component = file.entry.component.component_name
        if component not in components:
            components[component] = []
        path = str(file.file)
        components[component].append(path)

    for component, files in components.items():
        files_on_disk = listdir(join(root_path, component))
        for disk_file in files_on_disk:
            is_file_entry_file = False
            for file in files:
                if file.endswith(disk_file):
                    is_file_entry_file = True

            if not is_file_entry_file and ".ini" not in disk_file:  # ignore update.ini
                full_path = join(root_path, component, disk_file)
                unlink(full_path)


def get_random_string(length):
    # put your letters in the following string
    sample_letters = "abcdefghijklmnopqrstuvwxyz"
    result_str = "".join((random.choice(sample_letters) for i in range(length)))
    return result_str


def get_random_short_name():
    # put your letters in the following string
    return get_secret(5)


def get_secret(length=15):
    alphabet = string.ascii_letters + string.digits
    secret = "".join(secrets.choice(alphabet) for i in range(length))
    return secret


def get_free_tcp_port(
    max_tries=10, default_port=8000, not_allowed: list = [], maximum=65534
):
    port = default_port
    if port in not_allowed:
        port = random.randint(port, maximum)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for i in range(1, max_tries):
        try:
            if port in not_allowed:
                port = random.randint(port, maximum)
            s.connect(("localhost", int(port)))
            s.shutdown(2)
            port = random.randint(port, maximum)
        except:
            break
    return port

def set_state(id, message):
    models.state_map[id] = message

def bootstrap_reciever(root_path, server_obj, port, secret):
    try:
        set_state(server_obj.pk, "Downloading reciever release")
        r = get(RECIEVER_DOWNLOAD_FROM)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(root_path)
        set_state(server_obj.pk, "Extracted reciever release")
    except:
        set_state(server_obj.pk, "Extracted reciever release")
        return False

    reciever_path = join(root_path, "reciever")
    config = {
        "auth": secret,
        "debug": False,
        "host": "0.0.0.0",
        "port": port,
        "redownload_steam": False,
        "root_path": root_path,
    }
    set_state(server_obj.pk, "Doing APX reciever bootstrap")
    try:
        # TODO: find solution for admin issue
        got = subprocess.check_output(
            join(reciever_path, "reciever.bat"), cwd=reciever_path, shell=True
        ).decode("utf-8")
    except Exception as e:
        # Exceptions can't really handled at this point, so we are ignoring them
        set_state(server_obj.pk, str(e))

    # set ports
    other_servers = models.Server.objects.exclude(pk=server_obj.pk)
    occupied_ports_tcp = []
    occupied_ports_udp = []

    server_url_parts = urlparse(server_obj.url)
    server_parts = server_url_parts.netloc.split(":")
    server_host = server_parts[0]

    for server in other_servers:
        # locate host
        url_parts = urlparse(server.url)
        parts = url_parts.netloc.split(":")
        host = parts[0]

        if host == server_host:
            occupied_ports_tcp.append(server.http_port)
            occupied_ports_tcp.append(server.webui_port)
            occupied_ports_udp.append(server.sim_port)

    webui_port = random.randint(WEBUI_PORT_RANGE[0], WEBUI_PORT_RANGE[1])
    sim_port = random.randint(SIM_PORT_RANGE[0], SIM_PORT_RANGE[1])
    http_port = random.randint(HTTP_PORT_RANGE[0], HTTP_PORT_RANGE[1])

    # random, I trust you! most likely bad idea, but okay

    server_obj.sim_port = sim_port
    server_obj.http_port = http_port
    server_obj.webui_port = webui_port

    # create server.json
    set_state(server_obj.pk, "Done with bootstrap")
    server_obj.save()
    config_path = join(reciever_path, "server.json")

    # try to inject keypair
    key_file = join(BASE_DIR, "uploads", "keys")

    if exists(join(key_file, "ServerUnlock.bin")):
        set_state(server_obj.pk, "Injecting global keys")
        copyfile(
            join(key_file, "ServerUnlock.bin"),
            join(root_path, "server", "UserData", "ServerUnlock.bin"),
        )

    with open(config_path, "w") as file:
        file.write(dumps(config))
    
    for i in range(0, 10):
        try:
            key = get_server_hash(server_obj.url)
            set_state(server_obj.pk, "Trying to collect keys. Try {} of 10".format(i))
            key_root_path = join(MEDIA_ROOT, "keys", key)
            if not exists(key_root_path):
                mkdir(key_root_path)
            key_path = join(key_root_path, "ServerKeys.bin")
            relative_path = join("keys", key, "ServerKeys.bin")
            download_key_command = run_apx_command(
                key, "--cmd lockfile --args {}".format(key_path)
            )
            if exists(key_path):
                server_obj.server_key = relative_path
                server_obj.save()
                set_state(server_obj.pk, f"Ready for usage. Key was collected on try {i}")    
                break
            sleep(2)
        except Exception as e:
            set_state(server_obj.pk, f"Key collect try {i} of 10 failed: {e}")  



def get_hash(input):
    sha_1 = hashlib.sha1()
    sha_1.update(input.encode("utf-8"))
    key = str(sha_1.hexdigest())
    return key


def get_server_hash(url):
    return get_hash(url)


def run_apx_command(hashed_url, commandline):
    apx_path = join(APX_ROOT, "apx.py")
    python_path = "python.exe"
    local_python_path = join(BASE_DIR, "python.exe")
    if exists(local_python_path):
        python_path = local_python_path
    command_line = '"{}" "{}" --server {} {}'.format(
        python_path, apx_path, hashed_url, commandline
    )
    got = subprocess.check_output(command_line, cwd=APX_ROOT, shell=True).decode(
        "utf-8"
    )
    return got


def get_event_config(event_id: int):
    server = models.Event.objects.get(pk=event_id)
    ungrouped_vehicles = server.entries.all()
    signup_components = server.signup_components.all()
    vehicle_groups = {}
    entry_based_components_seen = []
    for vehicle in ungrouped_vehicles:
        component = vehicle.component
        key = component.pk
        steam_id = component.steam_id
        base_steam_id = base_steam_id = component.base_component.steam_id if component.base_component else 0
        version = "latest"
        name = component.component_name
        short_name = component.short_name
        is_official = component.is_official

        if key not in vehicle_groups:
            vehicle_groups[key] = {
                "entries": [],
                "entries_overwrites": {},
                "component": {
                    "base_steam_id": base_steam_id,
                    "steam_id": steam_id,
                    "version": version,
                    "name": name,
                    "update": True,
                    "official": is_official,
                    "short": short_name,
                    "numberplates": [],
                },
            }
        vehicle_groups[key]["entries"].append(
            "{}#{}:{}".format(
                vehicle.team_name, vehicle.vehicle_number, vehicle.pit_group
            )
        )
        if vehicle.additional_overwrites:
            props = {}
            lines = vehicle.additional_overwrites.split(linesep)
            pattern = r"^(.+)\s{0,}=\s{0,}\"(.+)\"$"
            for line in lines:
                got = match(pattern, line)
                if got:
                    props[got.group(1)] = got.group(2)
            vehicle_groups[key]["entries_overwrites"][
                vehicle.vehicle_number
            ] = props
        if vehicle.base_class:
            if (
                vehicle.vehicle_number
                not in vehicle_groups[key]["entries_overwrites"]
            ):
                vehicle_groups[key]["entries_overwrites"][
                    vehicle.vehicle_number
                ] = []
            vehicle_groups[key]["entries_overwrites"][vehicle.vehicle_number][
                "BaseClass"
            ] = vehicle.base_class
    if len(ungrouped_vehicles) == 0:
        # use signup components for the event.json
        for component in signup_components:
            key = component.pk
            steam_id = component.steam_id
            base_steam_id = component.base_component.steam_id if component.base_component else 0
            version = "latest"
            name = component.component_name
            short_name = component.short_name
            official = component.is_official

            if key not in vehicle_groups:
                vehicle_groups[key] = {
                    "entries": [],
                    "entries_overwrites": {},
                    "component": {
                        "base_steam_id": base_steam_id,
                        "steam_id": steam_id,
                        "version": version,
                        "name": name,
                        "update": False,
                        "short": short_name,
                        "official": official,
                        "numberplates": [],
                    },
                }
    tracks = server.tracks.all().order_by("-id")

    conditions = server.conditions

    track_groups = OrderedDict()
    for track in tracks:
        key = track.component.pk
        track_component = track.component
        steam_id = track.component.steam_id
        base_steam_id = track_component.base_component.steam_id if track_component.base_component else 0
        requires_update = models.TrackFile.objects.filter(track=track).count() > 0
        track_groups[key] = {
            "layout": track.layout,
            "component": {
                "base_steam_id": base_steam_id,
                "steam_id": steam_id,
                "version": "latest",
                "name": track_component.component_name,
                "update": requires_update,
                "official": track_component.is_official,
            },
        }
    if not server.mod_name or len(server.mod_name) == 0:
        mod_name = "apx_{}".format(get_server_hash(server.name)[:8])
    else:
        mod_name = server.mod_name
    # grip settings

    sessions = conditions.sessions.all()
    session_list = {}
    session_setting_list = []
    race_finish_criteria = None
    if len(sessions) > 0:
        for session in sessions:
            session_list[session.type] = session.grip.path if session.grip else None
            grip_scale = 1
            if "." not in str(session.real_road_time_scale):
                grip_scale = int(session.real_road_time_scale)
            else:
                grip_scale = float(session.real_road_time_scale)
            if str(session.type) == "R1" and session.race_finish_criteria:
                race_finish_criteria = int(session.race_finish_criteria)

            session_setting_list.append(
                {
                    "type": str(session.type),
                    "length": session.length,
                    "laps": session.laps,
                    "start": str(session.start) if session.start is not None else None,
                    "weather": session.weather,
                    "grip_needle": session.grip_needle,
                    "grip_scale": grip_scale,
                }
            )
    else:
        session_list = None

    start_type = 0
    if server.start_type == models.EvenStartType.FLS:
        start_type = 1
    if server.start_type == models.EvenStartType.SCR:
        start_type = 2
    if server.start_type == models.EvenStartType.FR:
        start_type = 4
    plugins = {}
    for plugin in server.plugins.all():
        name = basename(str(plugin.plugin_file))
        plugins[name] = loads(plugin.overwrites)
    mod_version = (
        server.event_mod_version
        if server.event_mod_version
        else "1.0.{}".format(get_random_string(5))
    )
    result = {
        "server": {
            "overwrites": {
                "Multiplayer.JSON": loads(server.multiplayer_json),
                "Player.JSON": loads(server.player_json),
            }
        },
        "include_stock_skins": server.include_stock_skins,
        "skip_all_session_unless_configured": server.skip_all_session_unless_configured,
        "conditions": session_list,
        "sessions": session_setting_list,
        "cars": vehicle_groups,
        "track": track_groups,
        "start_type": start_type,
        "real_weather": server.real_weather,
        "weather_api": server.weather_api,
        "weather_key": server.weather_key,
        "weather_uid": server.pk,
        "temp_offset": server.temp_offset,
        "comp": RECIEVER_COMP_INFO,
        "plugins": plugins,
        "race_finish_criteria": race_finish_criteria,
        "welcome_message": server.welcome_message,
        "mod": {
            "name": mod_name,
            "version": mod_version,
        },
    }
    return result


def do_post(message):
    if not message or len(message) == 0:
        return
    if DISCORD_WEBHOOK is not None and DISCORD_WEBHOOK_NAME is not None:
        got = post(
            DISCORD_WEBHOOK,
            json={
                "username": DISCORD_WEBHOOK_NAME,
                "content": message,
                "avatar_url": "",
            },
            headers={"Content-type": "application/json"},
        )

def do_embed_post(message, alternative_url=None):
    if not message or len(message) == 0:
        return
    if alternative_url is not None and len(alternative_url) > 0:
        got = post(
            alternative_url,
            json=message,
            headers={"Content-type": "application/json"},
        )
    if DISCORD_WEBHOOK is not None and DISCORD_WEBHOOK_NAME is not None:
        got = post(
            DISCORD_WEBHOOK,
            json=message,
            headers={"Content-type": "application/json"},
        )

def do_rc_post(message):
    if (
        DISCORD_RACE_CONTROL_WEBHOOK is not None
        and DISCORD_RACE_CONTROL_WEBHOOK_NAME is not None
    ):
        got = post(
            DISCORD_RACE_CONTROL_WEBHOOK,
            json={
                "username": DISCORD_RACE_CONTROL_WEBHOOK_NAME,
                "content": message,
                "avatar_url": "",
            },
            headers={"Content-type": "application/json"},
        )


def create_virtual_config():
    all_servers = models.Server.objects.all()
    server_data = {}
    for server in all_servers:
        key = get_server_hash(server.url)
        # we assume that the liveries folder may already be existing
        build_path = join(MEDIA_ROOT, "liveries")
        packs_path = PACKS_ROOT
        templates_path = join(MEDIA_ROOT, "templates")
        tracks_path = join(MEDIA_ROOT, "tracks")

        if not exists(packs_path):
            mkdir(packs_path)

        if not exists(build_path):
            mkdir(build_path)

        if not exists(templates_path):
            mkdir(templates_path)

        if not exists(tracks_path):
            mkdir(tracks_path)
        server_data[key] = {
            "url": server.url,
            "secret": server.secret,
            "env": {
                "build_path": build_path,
                "packs_path": packs_path,
                "templates_path": templates_path,
                "tracks_path": tracks_path,
            },
        }

    servers_json_path = join(APX_ROOT, "servers.json")
    with open(servers_json_path, "w") as file:
        file.write(dumps(server_data))


def degrees_to_direction(raw):
    val = int((raw / 22.5) + 0.5)
    arr = [
        "0",
        "1",
        "1",
        "2",
        "2",
        "3",
        "3",
        "4",
        "4",
        "5",
        "5",
        "6",
        "6",
        "7",
        "7",
        "0",
    ]
    return int(arr[(val % 16)])


def get_clouds(raw, rain=False):
    result = 0
    if rain:
        result = 5
    if raw <= 20:
        return result
    if raw > 20 and raw <= 40:
        return result + 1
    if raw > 40 and raw <= 60:
        return result + 2
    if raw > 60 and raw <= 80:
        return result + 3
    if raw >= 80 and raw <= 100:
        return result + 4


def update_weather(session):
    from requests import get
    import datetime
    from math import floor

    if session.start and session.track:
        forecast = get(
            "https://api.openweathermap.org/data/2.5/onecall?lat="
            + str(session.track.lat)
            + "&lon="
            + str(session.track.lon)
            + "&exclude=daily,current,minutely&appid="
            + OPENWEATHERAPI_KEY
            + "&units=metric"
        ).json()

        forecast_data = forecast["hourly"]
        start = int(session.start.hour)
        start_from_midnight = start * 60 + session.start.minute

        duration = (
            24 * 60
        )  # TODO: DEBUG IF THIS CAUSES ISSUES TO ADD 24h on each session
        end_time = start_from_midnight + duration

        starting_index = 0
        matching_forecast = []
        for index, forecast_entry in enumerate(forecast_data):
            # forecast is hourly, we only interested in the full hour numbers
            hour = int(
                datetime.datetime.fromtimestamp(forecast_entry["dt"]).strftime("%H")
            )
            if hour == start and starting_index == 0:
                starting_index = index

            if starting_index != 0 and len(matching_forecast) <= 24:
                matching_forecast.append(forecast_entry)

        last_rain = None
        weather_blocks = []
        for index, next_forecast in enumerate(matching_forecast):
            temp = floor(next_forecast["temp"])
            wind = floor(next_forecast["wind_speed"])
            wind_direction = degrees_to_direction(next_forecast["wind_deg"])

            block_length = (
                60  # 60 minutes block length, as the api does not delivery ynthing more
            )

            rain_volume = 0
            maximum_rain_volume = (
                300  # we assume that 30cm/hr ist the maximum amount of rain possible
            )
            # unit: mm per hour
            rain_percentage = 0
            if "rain" in next_forecast:
                rain_volume = next_forecast["rain"]["1h"]
                rain_percentage = floor(100 / (maximum_rain_volume / rain_volume))

            humidity = floor(next_forecast["humidity"])

            clouds = get_clouds(next_forecast["clouds"], rain_percentage > 20)
            start_time = start_from_midnight + index * 60
            day_max = 24 * 60
            if start_time > day_max:
                start_time = start_time - day_max

            rain_density = 0
            probability = next_forecast["pop"] * 100  # 0.0 > 1

            # as there is no propability -> randomize
            # 20 -> random 5 -> rain
            # 20 -> random 21 -> no rain

            match = random.randint(0, 100)

            # if the random number larger than the number, reset it
            # if the random number is lower than the one, let it rain!
            if match >= probability:
                rain_density = 0
                rain_percentage = 0

            if next_forecast["clouds"] > 80 and rain_percentage > 80:
                rain_density = 2
            block = {
                "HumanDate": str(datetime.datetime.fromtimestamp(next_forecast["dt"])),
                "Probability": floor(probability),
                "MatchedProbability": match,
                "StartTime": start_time,
                "Duration": block_length,
                "Sky": clouds,
                "RainChange": rain_percentage,
                "RainDensity": rain_density,
                "Temperature": temp,
                "Humidity": humidity,
                "WindSpeed": wind,
                "WindDirection": wind_direction,
            }
            last_rain = rain_percentage
            weather_blocks.append(block)

        wet_file_content = []
        for block in weather_blocks:
            wet_file_content.append("//Weather block real date: " + block["HumanDate"])
            wet_file_content.append("//POP=" + str(block["Probability"]))
            wet_file_content.append("//SERVERPOP=" + str(block["MatchedProbability"]))
            for line in [
                "StartTime",
                "Duration",
                "Sky",
                "RainChange",
                "RainDensity",
                "Temperature",
                "Humidity",
                "WindSpeed",
                "WindDirection",
            ]:
                wet_file_content.append(line + "=(" + str(block[line]) + ")")
        session.weather = linesep.join(wet_file_content)
        session.save()


def create_firewall_script(server):
    content = 'Remove-NetFirewallRule -DisplayName "APX RULE {}*"'.format(
        server.public_secret
    )

    content = content + "\n" + server.firewall_rules
    firewall_paths = join(BASE_DIR, "firewall_rules")
    if not exists(firewall_paths):
        mkdir(firewall_paths)
    path = join(BASE_DIR, firewall_paths, "firewall" + server.public_secret + ".ps1")
    with open(path, "w") as file:
        file.write(content)

    path = join(
        BASE_DIR, firewall_paths, "invoke_firewall" + server.public_secret + ".bat"
    )
    with open(path, "w") as file:
        content = (
            "@echo off\npowershell .\\firewall"
            + server.public_secret
            + ".ps1\necho Done adding rules\npause"
        )
        file.write(content)

def get_component_blob_for_discord(entry, is_vehicle, is_update=False, additional_text=""):
    description = "🖌 The server will provide a skin pack for this mod." if is_update else ""
    if not is_vehicle:
        description = "🖌 The server will provide a track update pack for this mod." if is_update else ""
    discord_blob = {
        "title": entry.component_name,			
        "fields": [],
        "color": 463186 if is_vehicle else 33791,
        "description": description
    }
    if entry.base_component is not None:
        discord_blob["fields"].append(
            {
                "name": "Link of required base mod",
                "value": "https://steamcommunity.com/sharedfiles/filedetails/?id={}".format( entry.base_component.steam_id) if  entry.base_component.steam_id > 0 else "Contact administrator for source",
                "inline": False
            }
        )
    
    discord_blob["fields"].append(
        {
            "name": "Base mod link",
            "value": "https://steamcommunity.com/sharedfiles/filedetails/?id={}".format(entry.steam_id) if entry.steam_id > 0 else "Contact administrator for source",
            "inline": False
        }
    )
    if additional_text != "":
        discord_blob["fields"].append(
            {
                "name": "Entries",
                "value": additional_text,
                "inline": False
            }
        )
    return discord_blob

def do_server_interaction(server):
    secret = server.secret
    url = server.url
    discord_url = server.discord_url
    set_state(server.pk, "-")
    server.save()
    key = get_server_hash(url)
    if server.action == "W":
        try:
            run_apx_command(key, "--cmd new_weekend")
        except Exception as e:
            print(e)
        finally:
            server.action = ""
            server.save()

    if server.action == "S+":
        set_state(server.pk, "Start requested")
        try:
            # update weather, if needed
            if server.event and server.event.real_weather:
                conditions = server.event.conditions
                for session in conditions.sessions.all():
                    update_weather(session)

                if server.update_weather_on_start:
                    event_config = get_event_config(server.event.pk)
                    event_config["branch"] = server.branch
                    event_config["update_on_build"] = server.update_on_build
                    event_config["callback_target"] = (
                        "{}addmessage/{}".format(PUBLIC_URL, server.public_secret)
                        if PUBLIC_URL
                        else None
                    )
                    config_path = join(APX_ROOT, "configs", key + ".json")
                    with open(config_path, "w") as file:
                        file.write(dumps(event_config))
                    command_line = "--cmd weatherupdate --args {}".format(config_path)

                    run_apx_command(key, command_line)
            run_apx_command(key, "--cmd start")
            # build the discord embed message
            json_blob = {
                "avatar_url": MSG_LOGO,
                "embeds": [
                    {
                        "title": "Server started",
                        "thumbnail": {
                            "url": MSG_LOGO
                        },
                        "color": 65404,
                        "fields": [
                            {
                                "name": "Name",
                                "value": "**"+server.event.name+"**",
                                "inline": True
                            },
                            {
                                "name": "Password",
                                "value": "`"+server.event.password+"`" if server.event.password else "No password",
                                "inline": True
                            },
                            {
                                "name": "Branch",
                                "value": "`"+server.branch+"`",
                                "inline": True
                            },
                            {
                                "name": "Content",
                                "value": "See below",
                                "inline": False
                            }
                        ]
                    }
                ]
            }
            #get files for tcars
            seen_components = []
            components_to_update = []
            entry_map = {}
            for vehicle in server.event.signup_components.all():
                if vehicle not in seen_components:
                    seen_components.append(vehicle)
                
            
            
            for vehicle in server.event.entries.all():
                # entry vehicles might be redundant, so create list first
                if vehicle.component not in seen_components:
                    seen_components.append(vehicle.component)
                else:
                    components_to_update.append(vehicle.component.pk)
                if vehicle.component.pk not in entry_map:
                    entry_map[vehicle.component.pk] = []
                entry_map[vehicle.component.pk].append("#{}: {}".format(vehicle.vehicle_number, vehicle.team_name))

            for component in seen_components:
                additional_text = ""
                if component.pk in entry_map:
                    addtional_text = "\n"
                    for entry in entry_map[component.pk]:
                        additional_text = additional_text + "\n" + entry
                json_blob["embeds"].append(get_component_blob_for_discord(component, True, component.pk in components_to_update, additional_text))

            for track in server.event.tracks.all():
                has_updates = models.TrackFile.objects.filter(track=track).count() > 0
                json_blob["embeds"].append(get_component_blob_for_discord(track.component, False, has_updates))
            do_embed_post(json_blob, discord_url)
        except Exception as e:
            print(e)
            set_state(server.pk, str(e))
            server.save()
        finally:
            set_state(server.pk, "-") 
            server.action = ""
            server.save()

    if server.action == "WU":
        try:
            event_config = get_event_config(server.event.pk)
            event_config["branch"] = server.branch
            event_config["update_on_build"] = server.update_on_build
            event_config["callback_target"] = (
                "{}addmessage/{}".format(PUBLIC_URL, server.public_secret)
                if PUBLIC_URL
                else None
            )
            config_path = join(APX_ROOT, "configs", key + ".json")
            with open(config_path, "w") as file:
                file.write(dumps(event_config))
            command_line = "--cmd weatherupdate --args {}".format(config_path)
            run_apx_command(key, command_line)

        except Exception as e:
            set_state(server.pk, str(e))
            server.save()
        finally:
            server.action = ""
            server.save()
    if server.action == "R-":
        set_state(server.pk, "Stop requested")
        try:
            run_apx_command(key, "--cmd stop")
            json_blob = {
                "avatar_url": MSG_LOGO,
                "embeds": [
                    {
                        "title": "Server stopped",
                        "thumbnail": {
                            "url": MSG_LOGO
                        },
                        "color": 16711680,
                        "fields": [
                            {
                                "name": "Name",
                                "value": "**"+server.event.name+"**",
                                "inline": True
                            }
                        ]
                    }
                ]
            }
            do_embed_post(json_blob, discord_url)
        except Exception as e:
            set_state(server.pk, str(e))
            server.save()
        finally:
            server.action = ""
            server.save()
            
            set_state(server.pk, "-") 

    if server.action == "D":
        set_state(server.pk, "Attempting to create event configuration")
        # save event json
        event_config = get_event_config(server.event.pk)
        # add ports
        event_config["server"]["overwrites"]["Multiplayer.JSON"][
            "Multiplayer General Options"
        ]["HTTP Server Port"] = int(server.http_port)
        event_config["server"]["overwrites"]["Multiplayer.JSON"][
            "Multiplayer General Options"
        ]["Simulation Port"] = int(server.sim_port)
        event_config["server"]["overwrites"]["Player.JSON"]["Miscellaneous"] = {}
        event_config["server"]["overwrites"]["Player.JSON"]["Miscellaneous"][
            "WebUI port"
        ] = server.webui_port
        event_config["suffix"] = (
            server.event.mod_version
            if server.event and server.event.mod_version
            else None
        )
        event_config["branch"] = server.branch
        event_config["weather_uid"] = server.pk
        event_config["heartbeat_only"] = server.heartbeat_only
        event_config["update_on_build"] = server.update_on_build
        event_config["callback_target"] = (
            "{}addmessage/{}".format(PUBLIC_URL, server.public_secret)
            if PUBLIC_URL
            else None
        )
        event_config["steamcmd_bandwidth"] = server.steamcmd_bandwidth
        event_config["collect_results_replays"] = server.collect_results_replays
        event_config["remove_cbash_shaders"] = server.remove_cbash_shaders
        event_config["remove_settings"] = server.remove_settings
        event_config["remove_unused_mods"] = server.remove_unused_mods

        if USE_GLOBAL_STEAMCMD:
            event_config["global_steam_path"] = join(BASE_DIR, "steamcmd")

        config_path = join(APX_ROOT, "configs", key + ".json")
        with open(config_path, "w") as file:
            file.write(dumps(event_config))
        # save rfm
        if not server.event.conditions.rfm:
            rfm_path = join(BASE_DIR, "default.rfm")
        else:
            rfm_path = join(MEDIA_ROOT, server.event.conditions.rfm.name)

        logger.info(f"Using {rfm_path} for this deployment")
        try:
            # check if track needs update
            for track in server.event.tracks.all():
                files = models.TrackFile.objects.filter(track=track)
                files_to_attach = []
                for file in files:
                    file_name = basename(str(file.file))
                    files_to_attach.append(file_name)
                # only add skin files if needed
                if len(files_to_attach) > 0:
                    set_state(server.pk, "Pushing track update to the server")
                    command_line = "--cmd build_track --args {} {}".format(
                        track.component.component_name, " ".join(files_to_attach)
                    )
                    run_apx_command(key, command_line)
            
            set_state(server.pk, "Pushing skins (if any) to the server")
            command_line = "--cmd build_skins --args {} {}".format(
                config_path, rfm_path
            )
            run_apx_command(key, command_line)

            set_state(server.pk, "Asking server for deployment")
            command_line = "--cmd deploy --args {} {}".format(config_path, rfm_path)
            run_apx_command(key, command_line)
            # push plugins, if needed
            plugin_args = ""
            for plugin in server.event.plugins.all():
                plugin_path = plugin.plugin_file.path
                target_path = plugin.plugin_path
                additional_path_arg = "\"|" + target_path + "\"" if target_path else "" 
                plugin_args = plugin_args + " " + plugin_path + additional_path_arg
            if len(plugin_args) > 0:
                set_state(server.pk, "Installing plugins")
                run_apx_command(key, "--cmd plugins --args " + plugin_args)
        except Exception as e:
            set_state(server.pk,str(e))
        finally:
            # build the discord embed message
            json_blob = {
                "avatar_url": MSG_LOGO,
                "embeds": [
                    {
                        "title": "Server update completed",
                        "thumbnail": {
                            "url": MSG_LOGO
                        },
                        "color": 16744192,
                        "fields": [
                            {
                                "name": "Name",
                                "value": "**"+server.event.name+"**",
                                "inline": True
                            }
                        ]
                    }
                ]
            }
            do_embed_post(json_blob, discord_url)
            server.action = ""
            server.save()

    # download server key, if needed:
    if not server.server_key:
        try:
            key_root_path = join(MEDIA_ROOT, "keys", key)
            if not exists(key_root_path):
                mkdir(key_root_path)
            key_path = join(key_root_path, "ServerKeys.bin")
            relative_path = join("keys", key, "ServerKeys.bin")
            download_key_command = run_apx_command(
                key, "--cmd lockfile --args {}".format(key_path)
            )
            if exists(key_path):
                server.server_key = relative_path
                server.save()
        except:
            print("{} does not offer a key".format(server.pk))

    # if an unlock key is present - attempt unlock!
    if server.server_unlock_key:
        try:
            key_root_path = join(MEDIA_ROOT, "keys", key)
            if not exists(key_root_path):
                mkdir(key_root_path)
            key_path = join(key_root_path, "ServerUnlock.bin")
            download_key_command = run_apx_command(
                key, "--cmd unlock --args {}".format(key_path)
            )
            server.server_unlock_key = None
        except Exception as e:
            print("{} unlock failed".format(server.pk))

        finally:
            server.save()