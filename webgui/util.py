from wizard.settings import APX_ROOT, MEDIA_ROOT, PACKS_ROOT
import hashlib
import subprocess
from os.path import join, exists
from os import mkdir
from . import models
from json import loads
import random
from django.core.exceptions import ValidationError

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
    "-icon-1024x576.png",
    "-icon-2048x1152.png",
]


def livery_filename(instance, filename):
    vehicle_number = instance.entry.vehicle_number
    component_short_name = instance.entry.component.short_name
    component_name = instance.entry.component.component_name
    component_path = join(MEDIA_ROOT, component_name)
    if not exists(component_path):
        mkdir(component_path)
    selected_suffix = None
    for suffix in FILE_NAME_SUFFIXES:
        if str(filename).endswith(suffix):
            selected_suffix = suffix
    if selected_suffix is None:
        raise ValidationError("We can't identify that file purpose")
    new_file_path = join(
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


def get_random_string(length):
    # put your letters in the following string
    sample_letters = "abcdefghi"
    result_str = "".join((random.choice(sample_letters) for i in range(length)))
    return result_str


def get_server_hash(url):
    sha_1 = hashlib.sha1()
    sha_1.update(url.encode("utf-8"))
    key = str(sha_1.hexdigest())
    return key


def run_apx_command(hashed_url, commandline):
    apx_path = join(APX_ROOT, "apx.py")
    command_line = "python {} --server {} {}".format(apx_path, hashed_url, commandline)
    got = subprocess.check_output(command_line, cwd=APX_ROOT).decode("utf-8")
    return got


def get_event_config(event_id: int):
    server = models.Event.objects.get(pk=event_id)
    ungrouped_vehicles = server.entries.all()
    vehicle_groups = {}
    for vehicle in ungrouped_vehicles:
        component = vehicle.component
        steam_id = component.steam_id
        version = component.component_version
        name = component.component_name
        do_update = component.do_update
        short_name = component.short_name

        if steam_id not in vehicle_groups:
            vehicle_groups[steam_id] = {
                "entries": [],
                "component": {
                    "version": version,
                    "name": name,
                    "update": do_update,
                    "short": short_name,
                    "numberplates": [],
                },
            }
        vehicle_groups[steam_id]["entries"].append(
            "{}#{}".format(vehicle.team_name, vehicle.vehicle_number)
        )

    tracks = server.tracks.all()

    conditions = server.conditions
    rfm_url = conditions.rfm.url

    track_groups = {}
    for track in tracks:
        track_component = track.component
        track_groups[track_component.steam_id] = {
            "layout": track.layout,
            "component": {
                "version": track_component.component_version,
                "name": track_component.component_name,
                "update": False,
            },
        }

    result = {
        "server": {
            "overwrites": {
                "Multiplayer.JSON": loads(server.overwrites_multiplayer),
                "Player.JSON": loads(server.overwrites_player),
            }
        },
        "cars": vehicle_groups,
        "track": track_groups,
        "mod": {
            "name": "apx_",
            "version": "1.0.{}".format(get_random_string(5)),
            "rfm": rfm_url,
        },
    }
    return result
