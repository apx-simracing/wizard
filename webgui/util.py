from wizard.settings import APX_ROOT
import hashlib
import subprocess
from os.path import join
from json import loads

from webgui.models import Event
import random

def get_random_string(length):
    # put your letters in the following string
    sample_letters = 'abcdefghi'
    result_str = ''.join((random.choice(sample_letters) for i in range(length)))
    return result_str

def get_server_hash(url):
    sha_1 = hashlib.sha1()
    sha_1.update(url.encode("utf-8"))
    key =  str(sha_1.hexdigest())
    return key

def run_apx_command(hashed_url, commandline):
  apx_path = join(APX_ROOT, "apx.py")
  command_line = "python {} --server {} {}".format(apx_path, hashed_url, commandline)
  got = subprocess.check_output(command_line, cwd=APX_ROOT).decode("utf-8")
  return got

def get_event_config(event_id: int):
  server = Event.objects.get(pk=event_id)
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
          "numberplates": []
        }
      }
    vehicle_groups[steam_id]["entries"].append("{}#{}".format(vehicle.team_name, vehicle.vehicle_number))
  
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
        "update": False
      }
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
      "version":"1.0.{}".format(get_random_string(5)),
      "rfm": rfm_url
    }
  }
  return result