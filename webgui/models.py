from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.conf import settings
from django import forms
from django.dispatch import receiver
from os.path import isfile
from shutil import copy
from os import remove
from json import loads
from django.core.validators import RegexValidator
from webgui.util import (
    livery_filename,
    run_apx_command,
    get_server_hash,
    get_key_root_path,
    get_logfile_root_path,
    get_conditions_file_root,
    get_update_filename,
    get_hash,
    get_livery_mask_root,
    get_random_string,
    create_virtual_config,
    do_server_interaction,
    get_component_file_root,
    remove_orphan_files,
    do_component_file_apply,
)
from wizard.settings import FAILURE_THRESHOLD, MEDIA_ROOT, STATIC_URL
from webgui.storage import OverwriteStorage
from django.utils.html import mark_safe
import re
from os.path import exists, join
from os import mkdir
from django.db.models.signals import post_save
from django.dispatch import receiver

from wand import image
from wand.drawing import Drawing
from wand.color import Color
from threading import Thread


class ComponentType(models.TextChoices):
    VEHICLE = "VEH", "Vehicle"
    LOCATION = "LOC", "Location"


class RaceSessionsType(models.TextChoices):
    TD = "TD", "Training Day"
    P1 = "P1", "Practice 1"
    Q1 = "Q1", "Qualy 1"
    WU = "WU", "Warmup"
    R1 = "R1", "Race 1"


alphanumeric_validator = RegexValidator(
    r"^[0-9a-zA-Z_]*$", "Only alphanumeric characters and dashes are allowed."
)


class Component(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=3, choices=ComponentType.choices, default=ComponentType.VEHICLE
    )
    steam_id = models.BigIntegerField(default=0, blank=True)
    component_version = models.CharField(
        default="1.0",
        max_length=20,
        help_text="The version to use. You can use 'latest' or 'latest-even' to either get the latest or the latest even version.",
    )
    component_name = models.CharField(
        default="Example_Mod", max_length=200, validators=[alphanumeric_validator]
    )
    do_update = models.BooleanField(
        default=False, help_text="If you plan to add liveries on a car, check this."
    )
    short_name = models.CharField(
        default="",
        max_length=200,
        help_text="The short name is required to idenitfy (livery) filenames belonging to this component. You only need this when 'Do update' is checked.",
        validators=[alphanumeric_validator],
    )

    update = models.FileField(
        upload_to=get_update_filename, storage=OverwriteStorage, null=True, blank=True
    )
    numberplate_template_l = models.FileField(
        upload_to=get_livery_mask_root,
        null=True,
        blank=True,
        max_length=255,
        help_text="A dds file containing the left numberplate background. Numbers will be applied.",
    )
    numberplate_template_mask_l = models.FileField(
        upload_to=get_livery_mask_root,
        null=True,
        blank=True,
        max_length=255,
        help_text="A dds file containing the region information for the left numberplate. Will be added on top of a given _Region.dds file.",
    )
    numberplate_template_r = models.FileField(
        upload_to=get_livery_mask_root,
        null=True,
        blank=True,
        max_length=255,
        help_text="A dds file containing the right numberplate background. Numbers will be applied.",
    )
    numberplate_template_mask_r = models.FileField(
        upload_to=get_livery_mask_root,
        null=True,
        blank=True,
        max_length=255,
        help_text="A dds file containing the region information for the leftright numberplate. Will be added on top of a given _Region.dds file.",
    )
    mask_positions = models.TextField(null=True, blank=True, default=None)

    template = models.TextField(default="", null=True, blank=True)

    files = models.ManyToManyField("ComponentFile", related_name="component_file_list")

    def clean(self):
        if self.type != ComponentType.VEHICLE and self.do_update:
            raise ValidationError(
                "Only vehicle components can currently recieve updates (for liveries)"
            )
        if self.type != ComponentType.VEHICLE and self.update:
            raise ValidationError("Only vehicle components can get an Update.ini file")

        if self.type == ComponentType.VEHICLE and self.do_update and not self.template:
            raise ValidationError("You will need the VEH template when doing an update")

    def save(self, *args, **kwargs):
        needles = ["number", "name", "description"]

        if self.type == ComponentType.VEHICLE and self.do_update and self.template:

            replacementMap = {
                "DefaultLivery": self.short_name + "_{number}.dds",
                "Number": "{number}",
                "Team": "{name}",
                "Description": "{description}",
                "FullTeamName": "{description}",
            }
            templateLines = self.template.split("\n")
            newLines = []
            for line in templateLines:
                hadReplacement = False
                for key, value in replacementMap.items():
                    pattern = r"(" + key + '\s{0,}=\s{0,}"?([^"^\n^\r]+)"?)'
                    matches = re.match(pattern, line, re.MULTILINE)
                    replacement = "{}={}\n".format(key, value)
                    if matches:
                        fullMatch = matches.groups(0)[0]
                        if '"' in fullMatch:
                            replacement = '{}="{}"\n'.format(key, value)

                        newLines.append(replacement)
                        hadReplacement = True
                if not hadReplacement:
                    newLines.append(line)

            self.template = "".join(newLines)
            # paste parsed template
            root_path = join(MEDIA_ROOT, get_hash(str(self.user.pk)), "templates")
            if not exists(root_path):
                mkdir(root_path)
            template_path = join(
                root_path,
                self.component_name + ".veh",
            )
            with open(template_path, "w") as file:
                file.write(self.template)
        super(Component, self).save(*args, **kwargs)

    def __str__(self):
        return "{} ({})".format(self.component_name, self.component_version)


class RaceSessions(models.Model):
    class Meta:
        verbose_name_plural = "Race sessions"

    description = models.TextField(default="Add description")
    type = models.CharField(
        max_length=2, choices=RaceSessionsType.choices, default=RaceSessionsType.TD
    )
    grip = models.FileField(
        upload_to=get_conditions_file_root,
        blank=False,
        null=False,
    )
    start = models.TimeField(
        blank=True,
        default=None,
        null=True,
        help_text="Target laps fro this session. This is in-game time. If empty, the defaults will be used.",
    )
    laps = models.IntegerField(default=0, help_text="Target laps of the session")
    length = models.IntegerField(
        default=0, help_text="Target length of the session in minutes"
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def clean(self):
        if self.length < 0 or self.laps < 0:
            raise ValidationError(
                "Either length or laps is negative. Set to 0 to ignore."
            )
        if "Q" not in str(self.type):
            if self.length > 0 and self.laps > 0:
                raise ValidationError(
                    "You cannot set laps and length of the session in one session"
                )
        if "WU" in str(self.type) and self.laps > 0:
            raise ValidationError("A warmup can only have a time lenght")

    def __str__(self):
        str = "[{}] {}, {} minutes, {} laps".format(
            self.type, self.description, self.length, self.laps
        )

        if self.start:
            return str + ", start: {}".format(self.start)
        else:
            return str


class RaceConditions(models.Model):
    class Meta:
        verbose_name_plural = "Race conditions"

    description = models.TextField(default="Add description")
    rfm = models.FileField(upload_to=get_conditions_file_root, storage=OverwriteStorage)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    sessions = models.ManyToManyField(RaceSessions, blank=True)

    def __str__(self):
        return "{} ({})".format(self.description, self.rfm)


class Track(models.Model):
    component = models.ForeignKey(Component, on_delete=models.DO_NOTHING)
    layout = models.CharField(default="", blank=False, max_length=200)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return "{}@{}".format(self.layout, self.component)


class Entry(models.Model):
    class Meta:
        verbose_name_plural = "Entries"

    component = models.ForeignKey(Component, on_delete=models.DO_NOTHING)
    team_name = models.CharField(default="Example Team", max_length=200)
    vehicle_number = models.CharField(default="1", max_length=3)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(
        default=None, null=True, blank=True, max_length=100, unique=True
    )

    def __str__(self):
        return "{}#{} ({})".format(self.team_name, self.vehicle_number, self.component)


class ComponentFileType(models.TextChoices):
    WINDOW = "window.dds", "Window skin (GT3)"
    WINDOWS = "windows.dds", "Window skin"
    WINDOWSIN = "windowsin.dds", "Windows (inside)"
    WINDOWSOUT = "windowsout.dds", "Windows (outside)"


class ComponentFile(models.Model):
    file = models.FileField(upload_to=get_component_file_root, max_length=500)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=50,
        choices=ComponentFileType.choices,
        default=ComponentFileType.WINDOW,
    )

    def __str__(self):
        return "{} {}: {}".format(self.component, self.type, self.file)


class EntryFile(models.Model):
    file = models.FileField(
        upload_to=livery_filename, storage=OverwriteStorage, max_length=500
    )
    entry = models.ForeignKey(
        Entry, on_delete=models.CASCADE, blank=False, null=False, default=None
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mask_added = models.BooleanField(
        default=False,
        help_text="Will be checked if a set of numberpaltes/ livery masks were added. Uncheck to force update.",
    )

    def __str__(self):
        return str(self.entry)

    def save(self, *args, **kwargs):
        needle = "{}_{}.dds".format(
            self.entry.component.short_name, self.entry.vehicle_number
        )

        regionNeedle = "{}_{}_Region.dds".format(
            self.entry.component.short_name, self.entry.vehicle_number
        )

        has_mask = (
            self.entry.component.update
            and self.entry.component.numberplate_template_r
            and self.entry.component.numberplate_template_mask_r
            and self.entry.component.numberplate_template_l
            and self.entry.component.numberplate_template_mask_l
        )

        if (
            (str(self.file).endswith(needle) or str(self.file).endswith(regionNeedle))
            and has_mask
            and not self.mask_added
            and self.pk
        ):
            # attempt numberplate addition
            livery_path = join(MEDIA_ROOT, str(self.file))

            # add the livery mask on top of thel ivery
            livery = image.Image(filename=livery_path, format="raw")
            livery.compression = "dxt5"

            is_region = livery_path.endswith("_Region.dds")

            numberplate_template_path_r = (
                self.entry.component.numberplate_template_r
                if not is_region
                else self.entry.component.numberplate_template_mask_r
            )

            numberplate_template_r = image.Image(
                filename=join(MEDIA_ROOT, str(numberplate_template_path_r)),
                format="raw",
            )

            numberplate_template_path_l = (
                self.entry.component.numberplate_template_l
                if not is_region
                else self.entry.component.numberplate_template_mask_l
            )

            numberplate_template_l = image.Image(
                filename=join(MEDIA_ROOT, str(numberplate_template_path_l)),
                format="raw",
            )

            numberplate_template_r.compression = "dxt5"
            numberplate_template_l.compression = "dxt5"
            numberplates = loads(self.entry.component.mask_positions)
            if numberplates is not None:
                for numberplate in numberplates:
                    side = numberplate["side"]
                    template = (
                        numberplate_template_l
                        if side.lower() == "l"
                        else numberplate_template_r
                    )
                    with template.clone() as rotate:
                        outer = numberplate["outer"]
                        inner = numberplate["inner"]
                        rotation = numberplate["rotate"]
                        color_id = numberplate["color"]
                        size = numberplate["size"]
                        flop = numberplate["flop"]
                        if flop:
                            rotate.flop()
                        if not is_region:
                            with Drawing() as draw:
                                color = Color(color_id)
                                draw.fill_color = color
                                draw.font_size = size
                                draw.color = color
                                draw.text(inner[0], inner[1], self.entry.vehicle_number)
                                draw(rotate)
                        if rotation > 0:
                            rotate.rotate(rotation, None)
                        livery.composite(rotate, left=outer[0], top=outer[1])

            livery.save(filename=livery_path)
            self.mask_added = True

        super(EntryFile, self).save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=EntryFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.file:
        if isfile(instance.file.path):
            remove(instance.file.path)


@receiver(models.signals.post_delete, sender=ComponentFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    remove_orphan_files(instance.user.pk)


@receiver(models.signals.post_save, sender=ComponentFile)
def auto_apply_comp_file(sender, instance, **kwargs):
    do_component_file_apply(instance)


# 0 Standing
# 1 formation lap & standing start
# 2 lap behind safety car & rolling start
# 4 fast rolling start


class EvenStartType(models.TextChoices):
    S = "S", "Standing start"
    FLS = "FLS", "Formation Lap and standing start"
    SCR = "SCR", "Lap behind safety car & rolling start"
    FR = "FR", "Fast rolling start"


class Event(models.Model):
    overwrites_multiplayer = models.TextField(default="{}")
    overwrites_player = models.TextField(default="{}")
    name = models.CharField(default="", max_length=200)
    conditions = models.ForeignKey(RaceConditions, on_delete=models.DO_NOTHING)
    entries = models.ManyToManyField(Entry)
    tracks = models.ManyToManyField(Track)
    signup_active = models.BooleanField(default=False)
    signup_components = models.ManyToManyField(Component)
    start_type = models.CharField(
        max_length=3, choices=EvenStartType.choices, default=EvenStartType.S
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    real_weather = models.BooleanField(
        default=False,
        help_text="Decides if real weather should be used. The weather is based on a hourly forecast.",
    )

    temp_offset = models.IntegerField(
        default=0,
        help_text="Adds a positive or negative number to the temperature in Celsius.",
    )

    mod_name = models.CharField(
        default="",
        blank=True,
        max_length=50,
        help_text="Name of the mod to install. If no value is given, the scheme apx_{randomstring} will be used. Max length is 50 chars.",
        validators=[alphanumeric_validator],
    )

    def __str__(self):
        return "{}".format(self.name)

    def clean(self):
        try:
            loads(self.overwrites_multiplayer)
        except:
            raise ValidationError(
                "The overwrites for the multiplayer.JSON are not valid"
            )
        try:
            loads(self.overwrites_player)
        except:
            raise ValidationError("The overwrites for the player.JSON are not valid")


class ServerStatus(models.TextChoices):
    STARTREQUESTED = "S+", "Start"
    STOPREQUESTED = "R-", "Stop"
    DEPLOY = "D", "Update config and redeploy"
    RESTARTWEEKEND = "W", "Restart weekend"


class ServerBranch(models.TextChoices):
    RC = "release-candidate", "release-candidate"
    P = "public", "public"


class Server(models.Model):
    name = models.CharField(
        blank=True,
        max_length=500,
        default="",
        null=True,
        help_text="A organistory name for the server",
    )
    url = models.CharField(
        blank=False, max_length=500, default="", help_text="The URL to the APX reciever"
    )
    secret = models.CharField(
        blank=False,
        max_length=500,
        default="",
        help_text="The secret for the communication with the APX reciever",
    )
    public_secret = models.CharField(
        blank=True,
        max_length=500,
        default=get_random_string(20),
        help_text="The secret for the communication with the APX race control",
    )
    public_ip = models.CharField(
        blank=False,
        max_length=500,
        default="",
        help_text="Not used currently. Use '0.0.0.0' if unkown.",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="The event to deploy. Note: You can only change this if the server is not running.",
    )
    action = models.CharField(
        max_length=3,
        choices=ServerStatus.choices,
        blank=True,
        default="",
        help_text="Runs an activity on the server.",
        verbose_name="Pending action to submit",
    )
    branch = models.CharField(
        max_length=50,
        choices=ServerBranch.choices,
        default=ServerBranch.P,
        blank=False,
        null=False,
        help_text="Public steam branch",
    )
    status = models.TextField(
        blank=True,
        null=True,
        default=None,
        help_text="Shows the reported status of the server. Can be empty or a JSON blob.",
    )
    locked = models.BooleanField(
        default=False,
        help_text="Shows if the server is currently processed by the background worker. During processing, you cannot change settings.",
        verbose_name="Processing pending action",
    )
    server_key = models.FileField(
        upload_to=get_key_root_path,
        help_text="Keyfile of the server. Will be filled automatically.",
        blank=True,
        default=None,
        null=True,
    )
    server_unlock_key = models.FileField(
        upload_to=get_key_root_path,
        help_text="Unlock keyfile of the server, usually named ServerUnlock.bin, required to use paid content. The field will clear after unlocking",
        blank=True,
        default=None,
        null=True,
    )
    log = models.FileField(
        upload_to=get_logfile_root_path,
        help_text="The logfile of the server for troublsehooting purposes",
        blank=True,
        default=None,
        null=True,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status_failures = models.IntegerField(
        default=0,
        help_text="The amount of failed status checks. The field will reset on save. If more than {} attemps will fail, the server will be ignored for status and actions..".format(
            FAILURE_THRESHOLD
        ),
    )

    @property
    def build(self):
        if self.status and "build" in self.status:
            content = loads(self.status.replace("'", '"'))
            return content["build"]
        else:
            return "-"

    @property
    def release(self):
        if self.status and "release" in self.status:
            content = loads(self.status.replace("'", '"'))
            return content["release"]
        else:
            return "-"

    @property
    def status_info(self):
        # no status to report (e. g. new server)
        response = '<img src="{}admin/img/icon-no.svg" alt="Not Running"> Server is not running</br>'.format(
            STATIC_URL
        )
        if self.status_failures >= FAILURE_THRESHOLD:
            response = '<img src="{}admin/img/icon-no.svg" alt="Not Running"> Server is disabled due to errors.</br>'.format(
                STATIC_URL
            )
        elif not self.status:
            response = '<img src="{}admin/img/icon-no.svg" alt="Not Running"> Server did not return a status yet</br>'.format(
                STATIC_URL
            )
        elif (
            self.status
            and "in_deploy" in self.status
            and self.status_failures <= FAILURE_THRESHOLD
        ):
            response = '<img src="{}admin/img/icon-no.svg" alt="Not Running"> The server is deploying</br>'.format(
                STATIC_URL
            )
        elif (
            self.status
            and "not_running" not in self.status
            and self.status_failures <= FAILURE_THRESHOLD
        ):
            response = '<img src="{}admin/img/icon-yes.svg" alt="Running"> Server is running</br>'.format(
                STATIC_URL
            )
            try:
                content = loads(self.status.replace("'", '"'))
                for vehicle in content["vehicles"]:
                    vehicle_text = "[{}] {}: {} (SteamID:{}), penalties: {}".format(
                        vehicle["carClass"],
                        vehicle["vehicleName"],
                        vehicle["driverName"],
                        vehicle["steamID"],
                        vehicle["penalties"],
                    )
                    response = response + vehicle_text + "</br>"
            except Exception as e:
                response = str(e)
        return mark_safe(response)

    def __str__(self):
        return self.url if not self.name else self.name

    def clean(self):
        if not self.server_key and self.action:
            raise ValidationError(
                "The server was not processed yet. Wait a short time until the key is present."
            )
        if (
            self.status is not None
            and "not_running" in self.status
            and self.action == "R-"
        ):
            raise ValidationError("The server is not running")

        if (
            self.status is not None
            and "not_running" not in self.status
            and self.action == "D"
        ):
            raise ValidationError("Stop the server first")

        if (
            self.status is not None
            and "not_running" not in self.status
            and self.action == "S+"
        ):
            raise ValidationError("Stop the server first")

        if self.action == "D" and not self.event:
            raise ValidationError("You have to add an event before deploying")

        if self.status and "in_deploy" in self.status:
            raise ValidationError("Wait until deployment is over")

        if self.action == "W" and self.status and "in_deploy" in self.status:
            raise ValidationError("Wait until deployment is over")

        if self.action == "W" and self.status and "not_running" in self.status:
            raise ValidationError("Start the server first")

        self.status_failures = 0

        if self.action != "":
            self.locked = True
            background_thread = Thread(
                target=background_action_server, args=(self,), daemon=True
            )
            background_thread.start()


def background_action_server(server):
    do_server_interaction(server)


def background_action_chat(chat):
    try:
        key = get_server_hash(chat.server.url)
        run_apx_command(key, "--cmd chat --args {} ".format(chat.message))
        chat.success = True
    except Exception as e:
        chat.success = False
    finally:
        chat.save()


@receiver(post_save, sender=Server)
def my_handler(sender, instance, **kwargs):
    create_virtual_config()


class Chat(models.Model):
    server = models.ForeignKey(Server, on_delete=models.DO_NOTHING)
    message = models.TextField(
        blank=True,
        null=True,
        default=None,
        max_length=50,
        help_text="Submits a message or a command to the given server. Can't be longer than 50 chars",
    )
    success = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return "{}@{}: {}".format(
            self.server, self.date.strftime("%m/%d/%Y, %H:%M:%S"), self.message
        )

    def clean(self):
        background_thread = Thread(
            target=background_action_chat, args=(self,), daemon=True
        )
        background_thread.start()


class ServerStatustext(models.Model):
    class Meta:
        verbose_name_plural = "Status history"

    status = models.TextField(
        blank=True,
        null=True,
        default=None,
        help_text="Shows the reported status of the server. Can be empty or a JSON blob.",
    )
    date = models.DateTimeField(auto_now_add=True)
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE, blank=False, null=False, default=None
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return "{} @ {}".format(self.server, self.date.strftime("%m/%d/%Y, %H:%M:%S"))