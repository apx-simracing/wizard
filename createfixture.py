target = "https://wiki.apx.chmr.eu/doku.php?id=common_components&do=export_text"
from requests import get
from json import dumps
from string import ascii_uppercase, digits
from random import choice

lines = get(target).text.split("\n")
data = []
component_index = 0
layouts_index = 0
for line in lines:
    parts = line.split(",")
    if len(parts) >= 2:
        component = parts[0].strip()
        steamid = parts[1].strip()
        layouts = None
        short_name = "".join(choice(ascii_uppercase + digits) for _ in range(5))
        if len(parts) > 2:
            layouts = parts[2:]
        if "Component" not in component:
            # avoid header
            component_index = component_index + 1
            new_tuple = {
                "model": "webgui.Component",
                "pk": component_index,
                "fields": {
                    "type": "VEH" if not layouts else "LOC",
                    "steam_id": steamid,
                    "component_name": component,
                    "short_name": short_name,
                },
            }

            data.append(new_tuple)
            if layouts:
                for layout in layouts:
                    layouts_index = layouts_index + 1
                    new_track = {
                        "model": "webgui.Track",
                        "pk": layouts_index,
                        "fields": {
                            "component": component_index,
                            "layout": layout.strip(),
                        },
                    }
                    data.append(new_track)

with open("common.json", "w") as file:
    parsed = dumps(data, sort_keys=True, indent=4)
    parsed = parsed.replace("\\u2013", "--")
    file.write(parsed)
