target = "https://wiki.apx.chmr.eu/doku.php?id=common_components&do=export_text"
from requests import get
from json import dumps

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
                    "component_version": "latest",
                    "component_name": component,
                    "short_name": component[0:8],
                    "user_id": 1,
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
                            "user_id": 1,
                        },
                    }
                    data.append(new_track)

with open("common.json", "w") as file:
    parsed = dumps(data, sort_keys=True, indent=4)
    parsed = parsed.replace("\\u2013", "--")
    file.write(parsed)
