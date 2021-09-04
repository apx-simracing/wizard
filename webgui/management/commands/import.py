from django.core.management.base import BaseCommand
from os.path import exists, join
from os import mkdir, listdir
from wizard.settings import BASE_DIR
from webgui.models import Component, Entry, EntryFile, TrackFile, Track
from webgui.util import FILE_NAME_SUFFIXES
from shutil import copyfile


class Command(BaseCommand):
    help = "Import data"

    def handle(self, *args, **options):
        kind_input = input('Name the kind of the content "track" or "vehicle": ')
        if kind_input not in ["track", "vehicle"]:
            raise Exception("Invalid input")
        import_path = join(BASE_DIR, "import")
        if not exists(import_path):
            mkdir(import_path)

        print(f"Importing: {kind_input}")
        short_name = input("Name a valid short name to identify the files: ")
        is_vehicle = kind_input == "vehicle"
        search_type = "VEH" if is_vehicle else "LOC"
        entries = Component.objects.filter(short_name=short_name, type=search_type)
        if entries.count() != 1:
            raise Exception(
                f"Did not manage to find a {kind_input} with short name {short_name}."
            )

        files = listdir(import_path)
        if not is_vehicle:
            layout = input("Name the layout: ")
            for file in files:
                track = Track.objects.get(component=entries.first(), layout=layout)
                track_file = TrackFile()
                track_file.track = track

                parent_path = join(
                    BASE_DIR,
                    "uploads",
                    "tracks",
                    track_file.track.component.component_name,
                )
                if not exists(parent_path):
                    mkdir(parent_path)
                relative_path = join(
                    "tracks", track_file.track.component.component_name, file
                )
                track_file.file = join(relative_path)
                source_path = join(BASE_DIR, "import", file)
                target_path = join(BASE_DIR, "uploads", relative_path)
                print(f"Copied {file} to {target_path}")
                track_file.save()
                copyfile(source_path, target_path)

        if is_vehicle:
            suffix = input(
                f"Do you have any chars between the {short_name} and the car number? If not, just press enter: "
            )

            prefix = short_name + suffix
            # search for vehicles matching the short name
            matched_files = list(filter(lambda x: prefix in x, files))

            # group files
            file_groups = {}

            for file in matched_files:
                file_without_prefix = file.replace(prefix, "")
                # attempt to find the name of the file without suffix and extensions

                for suffix in FILE_NAME_SUFFIXES:
                    lower_suffix = suffix.lower()
                    file_lower = file_without_prefix.lower()
                    only_number = file_lower.replace(lower_suffix, "")
                    if (
                        only_number != file_lower and "region" not in only_number
                    ):  # the file actually matched
                        if only_number not in file_groups:
                            file_groups[only_number] = []
                        if file not in file_groups[only_number]:
                            file_groups[only_number].append(file)

            for number, files in file_groups.items():
                print(f"Processing matches for car {number}")
                existing_entries = Entry.objects.filter(
                    component=entries.first(), vehicle_number=number
                )
                if existing_entries.count() == 1:
                    raise Exception("The entry is already existing for this component")
                e = Entry()
                e.component = entries.first()
                e.team_name = e.component.component_name
                e.vehicle_number = number
                e.save()
                for file in files:
                    print(f"Adding file {file} to entry of car {number}")
                    e_f = EntryFile()
                    e_f.entry = e
                    relative_path = join("liveries", e.component.component_name, file)
                    e_f.file = join(relative_path)
                    source_path = join(BASE_DIR, "import", file)
                    target_path = join(BASE_DIR, "uploads", relative_path)
                    print(f"Copied {file} to {target_path}")
                    e_f.save()
                    copyfile(source_path, target_path)
