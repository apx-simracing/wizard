from django.core.management.base import BaseCommand, CommandError
from webgui.models import Server, Entry, EntryFile
from os import listdir, mkdir
from shutil import move
from os.path import join, exists
from wizard.settings import MEDIA_ROOT

FILE_NAME_SUFFIXES = [
    "WINDOWSIN.dds",
    "WINDOWSOUT.dds",
    "_Region.dds",
    ".json",
    ".dds",
    "helmet.dds",
    "icon.png",
    "SMicon.dds",
    "icon.dds",
    "helmet.png",
    "-icon-128x72.png",
    "-icon-256x144.png",
    "-icon-1024x576.png",
    "-icon-2048x1152.png"
]

class Command(BaseCommand):
    help = 'Handle uploads and moves them into file structures'

    def handle(self, *args, **options):
        # Filesystem discovery

        entries = Entry.objects.all()
        files = listdir(MEDIA_ROOT)

        for entry in entries:
            component_name = entry.component.component_name
            component_path = join(MEDIA_ROOT, component_name)
            if not exists(component_path):
                self.stdout.write(self.style.SUCCESS('Creating component path for {}'.format(component_name)))
                            
                mkdir(component_path)
            
            short_name = entry.component.short_name

            file_name_needle =  "{}_{}".format(short_name, entry.vehicle_number)
            
            for discovered_file in files:
                full_path = join(MEDIA_ROOT, discovered_file)

                matches_needle = False

                for needle in FILE_NAME_SUFFIXES:
                    file_suffix = file_name_needle + needle
                    if discovered_file == file_suffix:
                        # file matches the  file suffix pattern
                        component_file_path_new = join(component_name, discovered_file)
                        entry_file = EntryFile.objects.filter(file__endswith=discovered_file).exclude(file__endswith=component_file_path_new).first()
                        
                        if entry_file is None:
                            # There is no known entry file yet
                            if not exists(join(MEDIA_ROOT, component_file_path_new)):
                                # there is no known file and there is now sorted file yet -> new file entry
                                self.stdout.write(self.style.SUCCESS('Adding new entry for {}'.format(discovered_file)))
                                entry_file = EntryFile()
                            else:
                                # there is a file but no entry for it -> existing one
                                entry_file = EntryFile.objects.filter(file__endswith=discovered_file).first()
                                
                                # we don't know the file entry yet -> new one 
                                if entry_file is None:
                                    self.stdout.write(self.style.SUCCESS('Adding new entry for existing file {}'.format(discovered_file)))
                                    entry_file = EntryFile()
                                else:
                                    self.stdout.write(self.style.SUCCESS('File exists, and entry file exists {}'.format(discovered_file)))
                                
                        else:
                            # use existing one
                            self.stdout.write(self.style.SUCCESS('Updating {} to {}'.format(entry_file.pk, component_file_path_new)))
                        entry_file.file = component_file_path_new
                        entry_file.entry = entry
                        entry_file.save()

                        
                        # move the file into the components folder
                        move(full_path, join(MEDIA_ROOT, component_file_path_new))


        # duplicate removal
        managed_files = EntryFile.objects.all()
        for row in managed_files:
            if EntryFile.objects.filter(file=row.file, entry=row.entry).count() > 1:
                self.stdout.write(self.style.SUCCESS('{} has a duplicate'.format(row)))
                row.delete()
        # mapping of entries in case there was no file changes, but some fiddling around within the website
        
        managed_files = EntryFile.objects.filter(entry=None).exclude(file=None)
        for row in managed_files:
            print(row)


        servers_to_deploy = Server.objects.filter(action="D")
        servers_to_start= Server.objects.filter(action="S+")
        servers_to_stop = Server.objects.filter(action="R-")