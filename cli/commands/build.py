from requests import post, get
from os.path import exists, join
from os import listdir
from json import load
import re
import tarfile
import io
import zipfile
from .util import http_api_helper
import logging

logger = logging.getLogger(__name__)


team_pattern = r"(?P<name>.+)\s?#(?P<number>.+)\:(?P<pitgroup>\d+)"


def get_final_filename(needle: str, short_name: str, number: str) -> str:
    final_name = f"{short_name}_{number}"
    if "windowsin" in needle or "windowin" in needle:
        final_name = f"{short_name}_{number}WINDOWSIN.dds"
    elif "windowout" in needle or "windowsout" in needle:
        final_name = f"{short_name}_{number}WINDOWSOUT.dds"
    elif "window" in needle:
        final_name = f"{short_name}_{number}WINDOW.dds"
    elif "region" in needle:
        final_name = f"{short_name}_{number}_Region.dds"
    elif ".json" in needle:
        final_name = f"{short_name}_{number}.json"
    elif ".dds" in needle:
        final_name = f"{short_name}_{number}.dds"
    elif "helmet.dds" in needle:
        final_name = f"{short_name}_{number}helmet.dds"
    elif "icon.png" in needle:
        final_name = f"{short_name}_{number}icon.png"
    elif "SMicon.dds" in needle:
        final_name = f"{short_name}_{number}SMicon.dds"
    elif "icon.dds" in needle:
        final_name = f"{short_name}_{number}icon.dds"
    elif "helmet.dds" in needle:
        final_name = f"{short_name}_{number}helmet.png"
    elif "-icon-128x72" in needle:
        final_name = f"{short_name}_{number}-icon-128x72.png"
    elif "-icon-256x144" in needle:
        final_name = f"{short_name}_{number}-icon-256x144.png"
    elif "-icon-1024x576" in needle:
        final_name = f"{short_name}_{number}-icon-1024x576.png"
    elif "-icon-2048x1152" in needle:
        final_name = f"{short_name}_{number}-icon-2048x1152.png"
    elif ".json" in needle:
        final_name = f"{short_name}_{number}.json"
    return final_name


def build_track_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        server_key = env["server"]
        server_data = env["server_data"][server_key]
        url = server_data["url"]
        secret = server_data["secret"]
        args_values = args[0]
        component = args_values[0]
        files = args_values[1:]

        tracks_path = server_data["env"]["tracks_path"]

        comp_path = join(tracks_path, component)
        if not exists(comp_path):
            raise FileNotFoundError("The component does not exists")

        existing_files = listdir(comp_path)

        attached_files = []
        for file in files:
            if file in existing_files:
                attached_files.append(file)

        if len(files) != len(attached_files):
            raise Exception("At least one file was not found")

        packs_path = server_data["env"]["packs_path"]

        output_filename = join(packs_path, f"server_{component}.tar.gz")
        with tarfile.open(output_filename, "w:gz") as tar:
            for file in attached_files:
                file_path = join(comp_path, file)
                tar.add(file_path, file)

        got = post(
            url + "/skins",
            headers={"authorization": secret},
            files={"skins": open(output_filename, "rb")},
            data={"target_path": component},
        )
        return True


def build_skin_command(env, *args, **kwargs):
    if not env["server"]:
        logger.info("no server set")
    else:
        server_key = env["server"]
        server_data = env["server_data"][server_key]
        url = server_data["url"]
        secret = server_data["secret"]
        file_name = args[0][0]
        if not exists(file_name):
            logger.info(f"file not exists: {file_name}")
        else:

            # read templates
            build_path = server_data["env"]["build_path"]
            packs_path = server_data["env"]["packs_path"]
            templates_path = server_data["env"]["templates_path"]

            templates = {}
            for file in listdir(templates_path):
                if file.endswith(".veh"):
                    with open(join(templates_path, file)) as file_handle:
                        templates[file.replace(".veh", "")] = file_handle.read()
            logger.info(f"Opening file: {file_name}")
            with open(file_name, "r") as file:
                data = load(file)
                veh_mods = data["cars"]
                for _, vehicle in veh_mods.items():
                    mod_name = vehicle["component"]["name"]
                    short_name = vehicle["component"]["short"]
                    entries = vehicle["entries"]
                    is_update = vehicle["component"]["update"]
                    if is_update:
                        output_filename = join(packs_path, f"server_{mod_name}.tar.gz")
                        with tarfile.open(output_filename, "w:gz") as tar:
                            for raw_file in listdir(join(build_path, mod_name)):
                                if ".zip" in raw_file:
                                    zip_path = join(build_path, mod_name, raw_file)
                                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                        zip_ref.extractall(join(build_path, mod_name))
                            all_files_in_build = list(filter(lambda x: "zip" not in x, listdir(join(build_path, mod_name))))

                            for raw_file in all_files_in_build:
                                if ".ini" in raw_file:
                                    tar.add(
                                        join(build_path, mod_name, raw_file), raw_file
                                    )
                                    logger.info(f"Adding {raw_file} to archive")
                                if ".png" in raw_file:
                                    tar.add(
                                        join(build_path, mod_name, raw_file), raw_file
                                    )
                                    logger.info(f"Adding {raw_file} to archive")
                            for entry in entries:
                                match = re.match(team_pattern, entry)
                                name = match.group("name").strip()
                                number = match.group("number").strip()
                                description = entry.split(":")[0]
                                pitgroup = match.group("pitgroup").strip()
                                # Parse the VEH file

                                if mod_name in templates:
                                    raw_template = templates[mod_name]
                                    parsed_template = eval(f'f"""{raw_template}\n"""')
                                    # add entry overwrites, if existing
                                    overwrites = (
                                        vehicle["entries_overwrites"][number]
                                        if number in vehicle["entries_overwrites"]
                                        else None
                                    )
                                    if overwrites:
                                        logger.info(
                                            "Found overwrites for VEH template for entry {}".format(
                                                number
                                            )
                                        )
                                        template_lines = parsed_template.split("\n")
                                        template_lines_with_overwrites = []
                                        for line in template_lines:
                                            line_to_add = None
                                            for key, value in overwrites.items():
                                                pattern = (
                                                    r"("
                                                    + key
                                                    + '\s{0,}=\s{0,}"?([^"^\n^\r]{0,})"?)'
                                                )
                                                matches = re.match(pattern, line)
                                                use_quotes = '"' in line
                                                if matches:
                                                    line_to_add = "{}={}\n".format(
                                                        key,
                                                        value
                                                        if not use_quotes
                                                        else '"{}"'.format(value),
                                                    )
                                                    logger.info(
                                                        "Using value {} (in quotes: {}) for key {} of entry {}".format(
                                                            value,
                                                            use_quotes,
                                                            key,
                                                            number,
                                                        )
                                                    )
                                                    break
                                            if line_to_add:
                                                template_lines_with_overwrites.append(
                                                    line_to_add
                                                )
                                            else:
                                                template_lines_with_overwrites.append(
                                                    line + "\n"
                                                )
                                        parsed_template = "".join(
                                            template_lines_with_overwrites
                                        )
                                    tar_template = parsed_template.encode("utf8")
                                    info = tarfile.TarInfo(
                                        name=f"{short_name}_{number}.veh"
                                    )
                                    info.size = len(tar_template)

                                file_pattern = r"([^\d]|_)" + number + "[^\d]"
                                # Collect livery files for this car
                                skin_files = []
                                had_custom_file = False
                                for build_file in all_files_in_build:
                                    if (
                                        re.search(file_pattern, build_file) is not None
                                        and ".veh" not in build_file
                                    ):
                                        skin_files.append(build_file)
                                for skin_file in skin_files:
                                    path = join(join(build_path, mod_name), skin_file)
                                    needle = skin_file.lower()
                                    final_name = skin_file
                                    had_custom_file = True
                                    tar.add(path, final_name)
                                    logger.info(f"Adding {final_name} to archive")

                                if had_custom_file and mod_name in templates:
                                    logger.info(f"Adding generated {info.name} to archive")
                                    tar.addfile(info, io.BytesIO(tar_template))

                        got = post(
                            url + "/skins",
                            headers={"authorization": secret},
                            files={"skins": open(output_filename, "rb")},
                            data={"target_path": mod_name},
                        )
                return True


def query_config(env, *args, **kwargs):
    got, text = http_api_helper(env, "config", {}, get)
    logger.info(text)
    return got


def get_config_command(env, *args, **kwargs) -> bool:
    got = query_config(env, args, kwargs)
    logger.info(got)
    return True


def get_ports_command(env, *args, **kwargs) -> bool:
    got = query_config(env, args, kwargs)
    simulation_port = int(got["Multiplayer General Options"]["Simulation Port"])
    http_port = int(got["Multiplayer General Options"]["HTTP Server Port"])
    reciever_port = int(got["reciever"]["port"])
    ports = {
        "TCP": [simulation_port, http_port, reciever_port],
        "UDP": [simulation_port, http_port + 1, http_port + 2],
    }
    logger.info(ports)
    return True
