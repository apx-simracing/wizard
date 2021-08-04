from wizard.settings import (
    APX_ROOT,
    MEDIA_ROOT,
    PACKS_ROOT,
    DISCORD_WEBHOOK,
    DISCORD_WEBHOOK_NAME,
    DISCORD_RACE_CONTROL_WEBHOOK,
    DISCORD_RACE_CONTROL_WEBHOOK_NAME,
    INSTANCE_NAME,
    OPENWEATHERAPI_KEY,
    BASE_DIR,
    PUBLIC_URL,
    BASE_DIR,
    MAX_STEAMCMD_BANDWIDTH,
    WEBUI_PORT_RANGE,
    HTTP_PORT_RANGE,
    SIM_PORT_RANGE,
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
import zipfile, io

FILE_NAME_SUFFIXES = [
    ".json",
    ".dds",
    "WINDOWSIN.dds",
    "WINDOWSOUT.dds",
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
]

FILE_NAME_SUFFIXES_MEANINGS = [
    "JSON file",
    "Livery main file",
    "Inner windows file",
    "Outer windows file",
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
]

RECIEVER_COMP_INFO = open(join(BASE_DIR, "release")).read()
RECIEVER_DOWNLOAD_FROM = "https://github.com/apx-simracing/reciever/releases/download/R65/reciever-2021R65.zip"


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
    component_short_name = instance.track.short_name
    component_name = instance.track.component_name
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


def do_component_file_apply(element):
    remove_orphan_files()
    root_path = join(MEDIA_ROOT, "liveries")
    existing_files = listdir(root_path)
    file_list = []
    component_files = {}
    component = element.component
    # group livery files per component
    if component.component_name not in component_files:
        component_files[component.component_name] = []
    if element.type not in component_files[component.component_name]:
        component_files[component.component_name].append(element.type)

    files = models.EntryFile.objects.filter(entry__component=component)
    for file in files:
        if file.file not in file_list:
            file_list.append(str(file.file))

    # remove existing component file additions
    for component, files in component_files.items():
        for file in files:
            comp_path = join(root_path, component)
            if exists(comp_path):
                component_files_existing = listdir(comp_path)
                for component_file in component_files_existing:
                    if component_file.endswith(file):
                        full_path = join(root_path, component, component_file)
                        unlink(full_path)

    # add component files
    template_root = join(MEDIA_ROOT)

    src_path = join(template_root, str(element.file))
    entries = models.Entry.objects.filter(component=element.component)
    if element.component.do_update:
        for entry in entries:
            target_path = join(
                root_path,
                element.component.component_name,
                element.component.short_name
                + "_"
                + str(entry.vehicle_number)
                + element.type,
            )
            copyfile(src_path, target_path)


def remove_orphan_files():
    root_path = join(MEDIA_ROOT, "liveries")
    files = models.EntryFile.objects.filter(entry__component__do_update=True)
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
    sample_letters = "abcdefghi"
    result_str = "".join((random.choice(sample_letters) for i in range(length)))
    return result_str


def get_secret(length=15):
    alphabet = string.ascii_letters + string.digits
    secret = "".join(secrets.choice(alphabet) for i in range(length))
    return secret


def get_free_tcp_port(max_tries=10, default_port=8000, not_allowed: list = []):
    port = default_port
    if port in not_allowed:
        port = random.randint(port, 65534)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for i in range(1, max_tries):
        try:
            if port in not_allowed:
                port = random.randint(port, 65534)
            s.connect(("localhost", int(port)))
            s.shutdown(2)
            port = random.randint(port, 65534)
        except:
            break
    return port


def bootstrap_reciever(root_path, server_obj, port, secret):
    try:
        server_obj.state = "Downloading reciever release"
        server_obj.save()
        r = get(RECIEVER_DOWNLOAD_FROM)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(root_path)
        server_obj.state = "Extracted reciever release"
        server_obj.save()
    except:
        server_obj.state = "Download for reciever failed"
        server_obj.save()
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
    server_obj.state = "Doing reciever bootstrap"
    server_obj.save()
    try:
        # TODO: find solution for admin issue
        got = subprocess.check_output(
            join(reciever_path, "reciever.bat"), cwd=reciever_path, shell=True
        ).decode("utf-8")
    except Exception as e:
        # Exceptions can't really handled at this point, so we are ignoring them
        pass

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
    server_obj.state = "Done with bootstrap"
    server_obj.save()
    config_path = join(reciever_path, "server.json")

    # try to inject keypair
    key_file = join(BASE_DIR, "uploads", "keys")

    if exists(join(key_file, "ServerKeys.bin")) and exists(
        join(key_file, "ServerUnlock.bin")
    ):
        server_obj.state = "Injecting global keys"
        server_obj.save()
        copyfile(
            join(key_file, "ServerKeys.bin"),
            join(root_path, "server", "UserData", "ServerKeys.bin"),
        )
        copyfile(
            join(key_file, "ServerUnlock.bin"),
            join(root_path, "server", "UserData", "ServerUnlock.bin"),
        )

    with open(config_path, "w") as file:
        file.write(dumps(config))
    try:
        for i in range(0, 5):
            server_obj.state = "Trying to collect keys. Try {} of 5".format(i)
            server_obj.save()
            do_server_interaction(server_obj)
        server_obj.state = "Ready for deployment"
        server_obj.save()
    except:
        server_obj.state = "Failed to collect keys"
        server_obj.save()


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
    command_line = "{} {} --server {} {}".format(
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
    for vehicle in ungrouped_vehicles:
        component = vehicle.component
        steam_id = component.steam_id
        version = component.component_version
        name = component.component_name
        do_update = component.do_update
        short_name = component.short_name
        is_official = component.is_official

        if steam_id not in vehicle_groups:
            vehicle_groups[steam_id] = {
                "entries": [],
                "entries_overwrites": {},
                "component": {
                    "version": version,
                    "name": name,
                    "update": do_update,
                    "official": is_official,
                    "short": short_name,
                    "numberplates": [],
                },
            }
        vehicle_groups[steam_id]["entries"].append(
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
            vehicle_groups[steam_id]["entries_overwrites"][
                vehicle.vehicle_number
            ] = props
    if len(ungrouped_vehicles) == 0:
        # use signup components for the event.json
        for component in signup_components:
            steam_id = component.steam_id
            version = component.component_version
            name = component.component_name
            do_update = component.do_update
            short_name = component.short_name
            official = component.is_official

            if steam_id not in vehicle_groups:
                vehicle_groups[steam_id] = {
                    "entries": [],
                    "entries_overwrites": {},
                    "component": {
                        "version": version,
                        "name": name,
                        "update": do_update,
                        "short": short_name,
                        "official": official,
                        "numberplates": [],
                    },
                }
    tracks = server.tracks.all()

    conditions = server.conditions

    track_groups = {}
    for track in tracks:
        track_component = track.component
        track_groups[track_component.steam_id] = {
            "layout": track.layout,
            "component": {
                "version": track_component.component_version,
                "name": track_component.component_name,
                "update": track_component.do_update,
                "official": track_component.is_official,
            },
        }
        break  # mutliple tracks are still not supported
    if not server.mod_name or len(server.mod_name) == 0:
        mod_name = "apx_{}".format(get_server_hash(server.name)[:8])
    else:
        mod_name = server.mod_name
    # grip settings

    sessions = conditions.sessions.all()
    session_list = {}
    session_setting_list = []
    if len(sessions) > 0:
        for session in sessions:
            session_list[session.type] = session.grip.path if session.grip else None
            session_setting_list.append(
                {
                    "type": str(session.type),
                    "length": session.length,
                    "laps": session.laps,
                    "start": str(session.start) if session.start is not None else None,
                    "weather": session.weather,
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
        "conditions": session_list,
        "sessions": session_setting_list,
        "cars": vehicle_groups,
        "track": track_groups,
        "start_type": start_type,
        "real_weather": server.real_weather,
        "temp_offset": server.temp_offset,
        "comp": RECIEVER_COMP_INFO,
        "plugins": plugins,
        "welcome_message": server.welcome_message,
        "mod": {
            "name": mod_name,
            "version": mod_version,
        },
    }
    return result


def do_post(message):
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


def do_server_interaction(server):
    secret = server.secret
    url = server.url
    key = get_server_hash(url)
    if server.action == "W":
        try:
            run_apx_command(key, "--cmd new_weekend")
            do_post(
                "[{}]: 🚀 Restart weekend looks good {}!".format(
                    INSTANCE_NAME, server.name
                )
            )
        except Exception as e:
            print(e)
            do_post(
                "[{}]: 😱 Failed to restart weekend {}: {}".format(
                    INSTANCE_NAME, server.name, str(e)
                )
            )
        finally:
            server.action = ""
            server.save()

    if server.action == "S+":
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
            do_post(
                "[{}]: 🚀 Starting looks complete for {}!".format(
                    INSTANCE_NAME, server.name
                )
            )
        except Exception as e:
            print(e)
            do_post(
                "[{}]: 😱 Failed starting server {}: {}".format(
                    INSTANCE_NAME, server.name, str(e)
                )
            )
        finally:
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
            print(e)
            do_post(
                "[{}]: 😱 Failed starting server {}: {}".format(
                    INSTANCE_NAME, server.name, str(e)
                )
            )
        finally:
            server.action = ""
            server.save()
    if server.action == "R-":

        try:
            run_apx_command(key, "--cmd stop")
            do_post(
                "[{}]: 🛑 Stopping looks complete for {}!".format(
                    INSTANCE_NAME, server.name
                )
            )
        except Exception as e:
            do_post(
                "[{}]: 😱 Failed to stop server {}: {}".format(
                    INSTANCE_NAME, server.name, str(e)
                )
            )
        finally:
            server.action = ""
            server.save()

    if server.action == "D":
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
        event_config["update_on_build"] = server.update_on_build
        event_config["callback_target"] = (
            "{}addmessage/{}".format(PUBLIC_URL, server.public_secret)
            if PUBLIC_URL
            else None
        )
        event_config["steamcmd_bandwidth"] = server.steamcmd_bandwidth
        event_config["collect_results_replays"] = server.collect_results_replays
        config_path = join(APX_ROOT, "configs", key + ".json")
        with open(config_path, "w") as file:
            file.write(dumps(event_config))
        # save rfm
        rfm_path = join(MEDIA_ROOT, server.event.conditions.rfm.name)

        try:
            # check if track needs update
            for track in server.event.tracks.all():
                if track.component.do_update:
                    files = models.TrackFile.objects.filter(track=track.component)
                    files_to_attach = []
                    for file in files:
                        file_name = basename(str(file.file))
                        files_to_attach.append(file_name)
                    command_line = "--cmd build_track --args {} {}".format(
                        track.component.component_name, " ".join(files_to_attach)
                    )
                    run_apx_command(key, command_line)
                break  # more than one at the moment not supported

            command_line = "--cmd build_skins --args {} {}".format(
                config_path, rfm_path
            )
            run_apx_command(key, command_line)
            command_line = "--cmd deploy --args {} {}".format(config_path, rfm_path)
            run_apx_command(key, command_line)
            # push plugins, if needed
            if server.event.plugins.count() > 0:
                files = ""
                for plugin in server.event.plugins.all():
                    files = files + " " + join(MEDIA_ROOT, str(plugin.plugin_file))
                command_line = "--cmd plugins --args {}".format(files)
                run_apx_command(key, command_line)
        except Exception as e:
            print(e)
        finally:
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
            do_post(
                "[{}]: Server {} - {} does not offer a key".format(
                    INSTANCE_NAME, server.pk, server.name
                )
            )

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

            do_post(
                "[{}]: Server {} - {} unlock failed: {}".format(
                    INSTANCE_NAME, server.pk, server.name, e
                )
            )

        finally:
            server.save()