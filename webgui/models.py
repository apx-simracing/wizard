from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.conf import settings
from django import forms
from django.dispatch import receiver
from os.path import isfile, basename
from shutil import copy, rmtree
from os import remove, linesep
from collections import OrderedDict
from json import loads
from django.contrib import messages
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from webgui.util import (
    livery_filename,
    track_filename,
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
    RECIEVER_COMP_INFO,
    get_plugin_root_path,
    create_firewall_script,
)
from wizard.settings import (
    FAILURE_THRESHOLD,
    MEDIA_ROOT,
    STATIC_URL,
    BASE_DIR,
    MAX_SERVERS,
    MAX_UPSTREAM_BANDWIDTH,
    MAX_DOWNSTREAM_BANDWIDTH,
    MAX_STEAMCMD_BANDWIDTH,
)
from webgui.storage import OverwriteStorage
from django.utils.html import mark_safe
import re
from os.path import exists, join
from os import mkdir, linesep
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta
import pytz
from json import dumps

USE_WAND = True
ADDPREFIX = True
try:
    from wand import image
    from wand.drawing import Drawing
    from wand.color import Color
except ImportError:
    USE_WAND = False
    print("Wand will not be available.")

from threading import Thread
from croniter import croniter
from re import match


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
    r"^[0-9a-zA-Z_-]*$", "Only alphanumeric characters and dashes are allowed."
)

alphanumeric_validator_dots = RegexValidator(
    r"^[0-9a-zA-Z.\%]*$", "Only alphanumeric characters and dots are allowed."
)


def event_name_validator(value):
    max_length = 26 if not ADDPREFIX else 21
    if len(value) > max_length:
        raise ValidationError(
            f"The event name is too long. You have {max_length} chars to use."
        )


class Component(models.Model):

    type = models.CharField(
        max_length=3, choices=ComponentType.choices, default=ComponentType.VEHICLE
    )
    steam_id = models.BigIntegerField(default=0, blank=True)
    component_name = models.CharField(
        default="Example_Mod", max_length=200, validators=[alphanumeric_validator]
    )
    is_official = models.BooleanField(
        default=False,
        help_text="Is official content which follows the even version and uneven version scheme (APX will select versions for you). If not checked, we will use the version you've selected.",
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

    def clean(self):
        if self.type != ComponentType.VEHICLE and self.update:
            raise ValidationError("Only vehicle components can get an Update.ini file")

    def save(self, *args, **kwargs):
        needles = ["number", "name", "description"]

        if self.type == ComponentType.VEHICLE and self.template:

            replacementMap = {
                "DefaultLivery": self.short_name + "_{number}.dds",
                "Number": "{number}",
                "Team": "{name}",
                "Description": "{description}",
                "FullTeamName": "{description}",
                "PitGroup": "Group{pitgroup}",
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
            root_path = join(MEDIA_ROOT, "templates")
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
        return self.component_name


class RaceSessions(models.Model):
    class Meta:
        verbose_name_plural = "Race sessions"

    description = models.CharField(default="Add description", max_length=200)
    type = models.CharField(
        max_length=2, choices=RaceSessionsType.choices, default=RaceSessionsType.TD
    )
    grip = models.FileField(
        upload_to=get_conditions_file_root, blank=True, null=True, default=None
    )
    grip_needle = models.CharField(
        default=None,
        null=True,
        blank=True,
        max_length=100,
        help_text="If you want to use the mod provided grip, add a filename/ and or part of the rrbin filename. If found, the uploaded grip file will be ignored.",
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
    weather = models.TextField(blank=True, null=True, default=None)
    track = models.ForeignKey("Track", on_delete=models.CASCADE, blank=True, null=True)

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

        if self.grip_needle and self.grip:
            raise ValidationError(
                "Grip and grip needle cannot be used at the same time"
            )

    def __str__(self):
        str = "[{}] {}, {} minutes, {} laps".format(
            self.type, self.description, self.length, self.laps
        )

        if self.track:
            str = str + f" [{self.track}]"

        if self.grip:
            str = str + ", gripfile: {}".format(basename(self.grip.name))
        if self.grip_needle:
            str = str + ", preset grip: {}".format(self.grip_needle)
        if self.start:
            return str + ", start: {}".format(self.start)
        else:
            return str


class RaceConditions(models.Model):
    class Meta:
        verbose_name_plural = "Race conditions"

    description = models.CharField(default="Add description", max_length=200)
    rfm = models.FileField(upload_to=get_conditions_file_root, storage=OverwriteStorage)

    sessions = models.ManyToManyField(RaceSessions, blank=True)

    def __str__(self):
        sessions = self.sessions.all()
        sessions_list = []
        for session in sessions:
            sessions_list.append(
                "{}@{} [{} minutes/{} laps]".format(
                    session.type,
                    session.start if session.start is not None else "Default startime",
                    session.length,
                    session.laps,
                )
            )
        return "{} ({})".format(
            self.description, "No sessions" if len(sessions) == 0 else sessions_list
        )


class Track(models.Model):
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    layout = models.CharField(default="", blank=False, max_length=200)

    lon = models.FloatField(
        default=None, blank=True, null=True, verbose_name="Longitute"
    )
    lat = models.FloatField(
        default=None, blank=True, null=True, verbose_name="Latitute"
    )
    section_list = models.TextField(
        blank=True, default=None, null=True, verbose_name="Track sections"
    )

    def __str__(self):
        return "{}@{}".format(self.layout, self.component)

    def clean(self):
        if self.section_list:
            # check if sections and points are valid
            lines = self.section_list.split(linesep)
            for line in lines:
                parts = line.split(";")
                if len(parts) < 2 or len(parts) > 3:
                    raise ValidationError(f"The parts are not valid. {line}")


class Entry(models.Model):
    class Meta:
        verbose_name_plural = "Entries"

    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    team_name = models.CharField(default="Example Team", max_length=200)
    vehicle_number = models.CharField(default="1", max_length=3)

    token = models.CharField(
        default=None, null=True, blank=True, max_length=100, unique=True
    )
    pit_group = models.IntegerField(
        default=1,
        help_text="The pit group for the entry. Stock tracks commonly using groups 1-30.",
    )
    additional_overwrites = models.TextField(
        blank=True,
        default=None,
        null=True,
        verbose_name="See Wiki article 'Wizard: Additional properties for entries' for details",
    )

    @property
    def events(self):
        events = Event.objects.filter(entries__in=[self.pk]).values_list(
            "name", flat=True
        )
        if len(events) == 0:
            return None
        return ", ".join(events)

    def clean(self):
        if not self.component.template:
            raise ValidationError(
                "Please add a template for the component {}".format(self.component)
            )

        # validate additional overwrites, if needed
        # we assume the \r\n as the wizard
        if self.additional_overwrites:
            lines = self.additional_overwrites.split(linesep)
            pattern = r"^(.+)\s{0,}=\s{0,}\"(.+)\"$"
            for line in lines:
                got = match(pattern, line)
                if not got:
                    raise ValidationError(
                        'The value for the line "{}" does not follow the scheme Name="Value"!'.format(
                            line
                        )
                    )

    def __str__(self):
        if self.events:
            return "{}#{} ({}) for {}".format(
                self.team_name, self.vehicle_number, self.component, self.events
            )
        else:
            return "{}#{} ({})".format(
                self.team_name, self.vehicle_number, self.component
            )


class TrackFile(models.Model):
    file = models.FileField(
        upload_to=track_filename, storage=OverwriteStorage, max_length=500
    )

    track = models.ForeignKey(
        Track, on_delete=models.CASCADE, blank=False, null=False, default=None
    )

    def __str__(self):
        return str(self.track) + ": " + str(self.file)


class EntryFile(models.Model):
    file = models.FileField(
        upload_to=livery_filename, storage=OverwriteStorage, max_length=500
    )
    entry = models.ForeignKey(
        Entry, on_delete=models.CASCADE, blank=False, null=False, default=None
    )

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
            and USE_WAND
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


# 0 Standing
# 1 formation lap & standing start
# 2 lap behind safety car & rolling start
# 4 fast rolling start


class EvenStartType(models.TextChoices):
    S = "S", "Standing start"
    FLS = "FLS", "Formation Lap and standing start"
    SCR = "SCR", "Lap behind safety car & rolling start"
    FR = "FR", "Fast rolling start"


class ServerPlugin(models.Model):
    plugin_file = models.FileField(
        upload_to=get_plugin_root_path,
        help_text="The plugin file",
        blank=False,
        default=None,
        null=False,
    )

    name = models.CharField(
        blank=True,
        max_length=500,
        default="",
        null=True,
        help_text="A organistory name for the plugin",
    )

    overwrites = models.TextField(
        default="{}",
        help_text="Additional JSON settings to use. ' Enabled: 1' will be added automatically.",
    )

    def __str__(self):
        return "{}: {}".format(self.name, basename(str(self.plugin_file)))

    def clean(self):
        try:
            loads(self.overwrites)
        except:
            raise ValidationError("This JSON is not valid.")


class EventRejoinRules(models.TextChoices):
    N = "0", "No rejoin"
    F = "1", "yes with fresh vehicle"
    S = "2", "yes with vehicle in same physical condition"
    SI = "3", "yes including setup"


class EventRejoinRules(models.TextChoices):
    N = "0", "No rejoin"
    F = "1", "yes with fresh vehicle"
    S = "2", "yes with vehicle in same physical condition"
    SI = "3", "yes including setup"


class EventFlagRules(models.TextChoices):
    N = "0", "None"
    P = "1", "Penalties only"
    PFC = "2", "Penalties & full-course yellows"
    EDQ = "3", "Everything except DQs"


class QualyMode(models.TextChoices):
    A = "0", "all cars qualify visibly on track together"
    O = "1", "only one car is visible at a time"
    R = "2", "use default from RFM, season, or track entry"


class BlueFlags(models.TextChoices):
    N = "0", "None"
    S = "1", "show but never penalize"
    P_0_3 = "2", "show and penalize if following within 0.3 seconds"
    P_0_5 = "3", "show and penalize if following within 0.5 seconds"
    P_0_7 = "4", "show and penalize if following within 0.7 seconds"
    P_0_9 = "5", "show and penalize if following within 0.7 seconds"
    P_1_1 = "6", "show and penalize if following within 1.1 seconds"
    R = "7", "Use rFm value"


class EventFailureRates(models.TextChoices):
    N = "0", "None"
    NOR = "1", "Normal"
    TS = "2", "Timescaled"


class QualyJoinMode(models.TextChoices):
    O = "0", "Open to all"
    P = "1", "Open but drivers will be pending an open session"
    C = "2", "closed"


class EventRaceTimeScale(models.TextChoices):
    P = "-1", "Race %"
    N = "0", "None"
    R = "1", "Normal"
    F2 = "2", "x2"
    F3 = "3", "x3"
    F4 = "4", "x4"
    F5 = "5", "x5"
    F10 = "10", "x10"
    F15 = "15", "x15"
    F20 = "20", "x20"
    F25 = "25", "x25"
    F30 = "30", "x30"
    F45 = "45", "x45"
    F60 = "60", "x60"


class Event(models.Model):
    name = models.CharField(
        default="",
        max_length=26,
        help_text="The Name of the event. Will be used as Race name in the server.",
        validators=[event_name_validator],
    )
    conditions = models.ForeignKey(
        RaceConditions,
        on_delete=models.CASCADE,
        help_text="Conditions is a bundle of session definitions, containing session lengths and grip information.",
    )
    entries = models.ManyToManyField(Entry, blank=True)
    tracks = models.ManyToManyField(Track)
    signup_active = models.BooleanField(default=False)
    signup_components = models.ManyToManyField(
        Component,
        help_text="Components allowed to be registered. If no entries are existing, all available entries from the mod will be used.",
    )

    include_stock_skins = models.BooleanField(
        default=False,
        help_text="Attempt to add stock skins even if own liveries are used.",
    )
    start_type = models.CharField(
        max_length=3, choices=EvenStartType.choices, default=EvenStartType.S
    )

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

    mod_version = models.CharField(
        default=None,
        null=True,
        blank=True,
        max_length=50,
        help_text="Version suffix to be used for content updates (track, cars). If not set, the value '.9apx' will be used.",
        validators=[alphanumeric_validator_dots],
    )

    event_mod_version = models.CharField(
        default="",
        blank=True,
        max_length=50,
        help_text="Version suffix to be used for the mod itself. If not set, a RANDOM value in concatenation with '1.0+{random}' will be used.",
        validators=[alphanumeric_validator_dots],
    )

    plugins = models.ManyToManyField(ServerPlugin, blank=True)

    timing_classes = models.TextField(
        default="{}",
        blank=True,
        help_text="JSON Config to rename classes, if needed",
    )
    welcome_message = models.TextField(
        default=None,
        null=True,
        blank=True,
        help_text="Welcome message",
    )

    """

    Session options

    """

    damage = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Damage multiplier",
    )

    password = models.CharField(
        default="",
        blank=True,
        max_length=50,
        help_text="Join password. Has max length of 50 chars.",
    )

    admin_password = models.CharField(
        default="apx",
        blank=False,
        null=False,
        max_length=50,
        help_text="Admin password. Has max length of 50 chars. Cannot be empty",
    )

    rejoin = models.CharField(
        max_length=50,
        choices=EventRejoinRules.choices,
        default=EventRejoinRules.N,
        blank=False,
        null=False,
        help_text="Race rejoin ruling",
    )

    rules = models.CharField(
        max_length=50,
        choices=EventFlagRules.choices,
        default=EventFlagRules.N,
        blank=False,
        null=False,
        help_text="Race rules",
    )

    race_multiplier = models.CharField(
        max_length=50,
        choices=EventRaceTimeScale.choices,
        default=EventRaceTimeScale.R,
        blank=False,
        null=False,
        help_text="Race time scale",
        verbose_name="Race time scale",
    )

    fuel_multiplier = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(7)],
        help_text="Fuel usage multiplier, use 0 to disable completely",
    )

    tire_multiplier = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(7)],
        help_text="Tire usage multiplier, use 0 to disable completely",
    )

    failures = models.CharField(
        max_length=50,
        choices=EventFailureRates.choices,
        default=EventFailureRates.N,
        blank=False,
        null=False,
        help_text="Mechanical failure rates",
    )

    clients = models.IntegerField(
        default=20,
        validators=[MinValueValidator(10), MaxValueValidator(109)],
        help_text="Allowed clients",
    )

    ai_clients = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(109)],
        help_text="Allowed AI clients",
    )

    real_name = models.BooleanField(
        default=False,
        help_text="Decides if the server forces the client to expose the real name",
    )

    downstream = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000000)],
        help_text="Downstream in KBPS. Calculate with 2000 per client.",
    )

    upstream = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000000)],
        help_text="Upstream in KBPS. Calculate with 2000 per client.",
    )

    replays = models.BooleanField(
        default=False,
        help_text="Enable or disable replays for this event",
    )

    """
        Allowed driving aids
    """

    allow_traction_control = models.IntegerField(
        default=3,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="Allow traction control",
    )

    allow_anti_lock_brakes = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Allow Anti-Lock Braking",
    )

    allow_stability_control = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Allow Stability Control",
    )

    allow_auto_shifting = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="Allow Stability Control",
    )

    allow_steering_help = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="Allow steering help",
    )

    allow_braking_help = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Allow braking help",
    )

    allow_auto_clutch = models.BooleanField(
        default=True,
        help_text="Allow auto clutch",
    )

    allow_invulnerability = models.BooleanField(
        default=False,
        help_text="Allow Invulnerability",
    )

    allow_auto_pit_stop = models.BooleanField(
        default=False,
        help_text="Allow auto pit stop",
    )

    allow_opposite_lock = models.BooleanField(
        default=False,
        help_text="Allow opposite lock",
    )

    allow_spin_recovery = models.BooleanField(
        default=False,
        help_text="Allow spin recovery",
    )

    allow_ai_toggle = models.BooleanField(
        default=False,
        help_text="Allow AI toggle",
    )

    cuts_allowed = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Track cuts allowed before a penalty is given",
    )

    qualy_mode = models.CharField(
        max_length=50,
        choices=QualyMode.choices,
        default=QualyMode.R,
        blank=False,
        null=False,
        help_text="Qualy mode",
    )

    blue_flag_mode = models.CharField(
        max_length=50,
        choices=BlueFlags.choices,
        default=BlueFlags.S,
        blank=False,
        null=False,
        help_text="Blue flag mode",
    )

    pause_while_zero_players = models.BooleanField(
        default=False,
        help_text="Pause while zero players",
    )

    pit_speed_override = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="pitlane speed limit override in meters/sec (0=disabled)",
    )

    must_be_stopped = models.BooleanField(
        default=False,
        help_text="Whether drivers must come to a complete stop before exiting back to the monitor",
    )

    qualy_join_mode = models.CharField(
        max_length=50,
        choices=QualyJoinMode.choices,
        default=QualyJoinMode.O,
        blank=False,
        null=False,
        help_text="Closed Qualify Sessions",
    )

    after_race_delay = models.IntegerField(
        default=90,
        validators=[MinValueValidator(0)],
        help_text="Dedicated server additional delay (added to delay between sessions before loading next track",
    )

    delay_between_sessions = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0)],
        help_text="Dedicated server delay before switching sessions automatically (after hotlaps are completed, if option is enabled), previously hardcoded to 45",
    )

    collision_fade_threshold = models.FloatField(
        default=0.7,
        help_text="Collision impacts are reduced to zero at this latency",
    )

    @property
    def multiplayer_json(self):
        blob = OrderedDict()
        blob["Multiplayer Server Options"] = OrderedDict()
        blob["Multiplayer Server Options"]["Join Password"] = self.password
        blob["Multiplayer Server Options"]["Admin Password"] = self.admin_password
        blob["Multiplayer Server Options"]["Race Rejoin"] = int(self.rejoin)
        blob["Multiplayer Server Options"]["Max MP Players"] = self.clients
        blob["Multiplayer Server Options"]["Maximum AI"] = self.ai_clients
        if self.clients > 50:
            blob["Multiplayer Server Options"]["Lessen Restrictions"] = True
        blob["Multiplayer Server Options"]["Enforce Real Name"] = self.real_name
        blob["Multiplayer Server Options"]["Default Game Name"] = (
            "[APX] {}".format(self.name[0:20]) if ADDPREFIX else self.name
        )

        # control aids
        blob["Multiplayer Server Options"][
            "Allowed Traction Control"
        ] = self.allow_traction_control
        blob["Multiplayer Server Options"][
            "Allowed Antilock Brakes"
        ] = self.allow_anti_lock_brakes
        blob["Multiplayer Server Options"][
            "Allowed Stability Control"
        ] = self.allow_stability_control
        blob["Multiplayer Server Options"][
            "Allowed Auto Shift"
        ] = self.allow_auto_shifting
        blob["Multiplayer Server Options"][
            "Allowed Steering Help"
        ] = self.allow_steering_help
        blob["Multiplayer Server Options"][
            "Allowed Brake Help"
        ] = self.allow_braking_help
        blob["Multiplayer Server Options"][
            "Allowed Auto Clutch"
        ] = self.allow_auto_clutch
        blob["Multiplayer Server Options"][
            "Allowed Invulnerability"
        ] = self.allow_invulnerability
        blob["Multiplayer Server Options"][
            "Allowed Auto Pit"
        ] = self.allow_auto_pit_stop
        blob["Multiplayer Server Options"][
            "Allowed Opposite Lock"
        ] = self.allow_opposite_lock
        blob["Multiplayer Server Options"][
            "Allowed Spin Recovery"
        ] = self.allow_spin_recovery
        blob["Multiplayer Server Options"]["Allow AI Toggle"] = self.allow_ai_toggle

        blob["Multiplayer General Options"] = OrderedDict()
        blob["Multiplayer General Options"]["Download Custom Skins"] = False
        blob["Multiplayer General Options"]["Net Connection Type"] = 6
        blob["Multiplayer General Options"]["Downstream Rated KBPS"] = self.downstream
        blob["Multiplayer General Options"]["Upstream Rated KBPS"] = self.upstream

        blob["Multiplayer Server Options"][
            "Pause While Zero Players"
        ] = self.pause_while_zero_players

        blob["Multiplayer Server Options"]["Must Be Stopped"] = self.must_be_stopped
        blob["Multiplayer Server Options"][
            "Closed Qualify Sessions"
        ] = self.qualy_join_mode
        blob["Multiplayer Server Options"]["Delay After Race"] = self.after_race_delay
        blob["Multiplayer Server Options"][
            "Delay Between Sessions"
        ] = self.delay_between_sessions
        blob["Multiplayer Server Options"][
            "Collision Fade Thresh"
        ] = self.collision_fade_threshold

        return dumps(blob)

    @property
    def player_json(self):
        blob = OrderedDict()
        blob["Game Options"] = OrderedDict()
        blob["Game Options"]["MULTI Damage Multiplier"] = self.damage
        blob["Game Options"]["Record Replays"] = self.replays
        blob["Game Options"]["CURNT Fuel Consumption Multiplier"] = int(
            self.fuel_multiplier
        )
        blob["Game Options"]["GPRIX Fuel Consumption Multiplier"] = int(
            self.fuel_multiplier
        )
        blob["Game Options"]["MULTI Fuel Consumption Multiplier"] = int(
            self.fuel_multiplier
        )
        blob["Game Options"]["RPLAY Fuel Consumption Multiplier"] = int(
            self.fuel_multiplier
        )
        blob["Game Options"]["CHAMP Fuel Consumption Multiplier"] = int(
            self.fuel_multiplier
        )

        blob["Game Options"]["CURNT Tire Wear Multiplier"] = int(self.tire_multiplier)
        blob["Game Options"]["GPRIX Tire Wear Multiplier"] = int(self.tire_multiplier)
        blob["Game Options"]["MULTI Tire Wear Multiplier"] = int(self.tire_multiplier)
        blob["Game Options"]["RPLAY Tire Wear Multiplier"] = int(self.tire_multiplier)
        blob["Game Options"]["CHAMP Tire Wear Multiplier"] = int(self.tire_multiplier)

        blob["Game Options"]["Record Replays"] = self.replays

        blob["Race Conditions"] = OrderedDict()
        if self.real_weather:
            blob["Race Conditions"]["MULTI Weather"] = 5
            blob["Race Conditions"]["GPRIX Weather"] = 5
        blob["Race Conditions"]["MULTI Flag Rules"] = int(self.rules)
        blob["Race Conditions"]["RPLAY Flag Rules"] = int(self.rules)
        blob["Race Conditions"]["CHAMP Flag Rules"] = int(self.rules)
        blob["Race Conditions"]["CURNT Flag Rules"] = int(self.rules)
        blob["Race Conditions"]["GPRIX Flag Rules"] = int(self.rules)

        blob["Race Conditions"]["MULTI RaceTimeScale"] = int(self.race_multiplier)
        blob["Race Conditions"]["RPLAY RaceTimeScale"] = int(self.race_multiplier)
        blob["Race Conditions"]["CHAMP RaceTimeScale"] = int(self.race_multiplier)
        blob["Race Conditions"]["CURNT RaceTimeScale"] = int(self.race_multiplier)
        blob["Race Conditions"]["GPRIX RaceTimeScale"] = int(self.race_multiplier)

        blob["Race Conditions"]["MULTI Track Cuts Allowed"] = int(self.cuts_allowed)
        blob["Race Conditions"]["RPLAY Track Cuts Allowed"] = int(self.cuts_allowed)
        blob["Race Conditions"]["CHAMP Track Cuts Allowed"] = int(self.cuts_allowed)
        blob["Race Conditions"]["CURNT Track Cuts Allowed"] = int(self.cuts_allowed)
        blob["Race Conditions"]["GPRIX Track Cuts Allowed"] = int(self.cuts_allowed)

        blob["Race Conditions"]["MULTI PrivateQualifying"] = int(self.qualy_mode)
        blob["Race Conditions"]["RPLAY PrivateQualifying"] = int(self.qualy_mode)
        blob["Race Conditions"]["CHAMP PrivateQualifying"] = int(self.qualy_mode)
        blob["Race Conditions"]["CURNT PrivateQualifying"] = int(self.qualy_mode)
        blob["Race Conditions"]["GPRIX PrivateQualifying"] = int(self.qualy_mode)

        blob["Race Conditions"]["MULTI BlueFlags"] = int(self.blue_flag_mode)
        blob["Race Conditions"]["RPLAY BlueFlags"] = int(self.blue_flag_mode)
        blob["Race Conditions"]["CHAMP BlueFlags"] = int(self.blue_flag_mode)
        blob["Race Conditions"]["CURNT BlueFlags"] = int(self.blue_flag_mode)
        blob["Race Conditions"]["GPRIX BlueFlags"] = int(self.blue_flag_mode)

        return dumps(blob)

    def __str__(self):
        return "{}".format(self.name)

    def clean(self, *args, **kwargs):
        if self.admin_password == "apx":
            raise ValidationError("Please set the admin password.")
        if self.downstream == 0:
            raise ValidationError("The downstream cannot be 0.")
        if self.upstream == 0:
            raise ValidationError("The upstream cannot be 0.")
        if self.welcome_message:
            parts = self.welcome_message.split(linesep)
            for part in parts:
                if len(part) > 50:
                    raise ValidationError(
                        "Limit the line length of each line of the welcome text to 50!"
                    )


class ServerStatus(models.TextChoices):
    STARTREQUESTED = "S+", "Start"
    STOPREQUESTED = "R-", "Stop"
    DEPLOY = "D", "Update config and redeploy"
    RESTARTWEEKEND = "W", "Restart weekend"
    WEATHERUPDATE = "WU", "Weather forecast update"


class ServerBranch(models.TextChoices):
    RC = "release-candidate", "release-candidate"
    P = "public", "public"
    PR = "previous-release", "previous-release"
    V21 = "v1121", "v1121"
    V22 = "v1122", "v1122"
    OLD = "old-ui", "old-ui"


class Server(models.Model):

    webui_port = models.IntegerField(
        default=1025,
        validators=[MinValueValidator(1025), MaxValueValidator(65535)],
        help_text="Port for the webui_port. Must be unique on all managed servers",
    )

    sim_port = models.IntegerField(
        default=54297,
        validators=[MinValueValidator(1025), MaxValueValidator(65535)],
        help_text="Port for the Simulation. Must be unique on all managed servers",
    )

    http_port = models.IntegerField(
        default=64297,
        validators=[MinValueValidator(1025), MaxValueValidator(65535)],
        help_text="Port for the HTTP Server. Must be unique on all managed servers",
    )
    steamcmd_bandwidth = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000000)],
        help_text="Limit the bandwidth steamcmd may use. 0 means unlimited download. Value is kbit/s. Maximum is 1000000",
    )
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
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
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
    server_key = models.FileField(
        upload_to=get_key_root_path,
        help_text="Keyfile of the server. Will be filled on save",
        blank=True,
        default=None,
        null=True,
    )
    server_unlock_key = models.FileField(
        upload_to=get_key_root_path,
        help_text="Unlock keyfile of the server, usually named ServerUnlock.bin, required to use paid content. The field will cleared after unlocking",
        blank=True,
        default=None,
        null=True,
    )
    update_on_build = models.BooleanField(
        default=False,
        help_text="Decides if APX will call dedicated server update when refreshing the content",
    )
    update_weather_on_start = models.BooleanField(
        default=False,
        help_text="Decides if APX will update the weather data on start if real weather is enabled",
    )
    collect_results_replays = models.BooleanField(
        default=False,
        help_text="Decides if APX will allow the server to persist the result and replay files",
    )
    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="APX Session Id",
    )
    status = models.TextField(blank=True, null=True, default=None)
    state = models.TextField(
        blank=True,
        null=True,
        default=None,
        help_text="The last update info got from the reciever",
    )

    @property
    def logfile(self):
        key = get_server_hash(self.url)
        path = join(MEDIA_ROOT, "logs", key, "reciever.log")
        contents = None
        if exists(path):
            with open(path, "r") as file:
                contents = file.read()
        return contents

    @property
    def is_created_by_apx(self):
        path = join(BASE_DIR, "server_children", self.public_secret)
        return exists(path)

    @property
    def firewall_rules(self):
        rules = ""

        name = self.public_secret
        for port in [self.sim_port, self.http_port]:
            rules = (
                rules
                + f'New-NetFirewallRule -DisplayName "APX RULE {name} ({port} TCP)" -Direction Inbound -LocalPort {port} -Protocol TCP -Action Allow\n'
            )
        for port in [self.sim_port, self.http_port + 1, self.http_port + 2]:
            rules = (
                rules
                + f'New-NetFirewallRule -DisplayName "APX RULE {name} ({port} UDP)" -Direction Inbound -LocalPort {port} -Protocol UDP -Action Allow\n'
            )
        return rules

    @property
    def ports(self):
        return "TCP: {}, {}/ UDP: {}, {}, {}".format(
            self.sim_port,
            self.http_port,
            self.sim_port,
            self.http_port + 1,
            self.http_port + 2,
        )

    @property
    def status_info(self):
        status = self.status
        if self.state and not self.status:
            if "failed" in self.state or "Exception" in self.state:
                return mark_safe(
                    '<img src="{}admin/img/icon-no.svg" alt="Not Running"> {}</br>'.format(
                        STATIC_URL, self.state
                    )
                )
            return self.state
        # no status to report (e. g. new server)
        response = '<img src="{}admin/img/icon-no.svg" alt="Not Running"> Server is not running</br>'.format(
            STATIC_URL
        )

        if not status:
            response = '<img src="{}admin/img/icon-no.svg" alt="Not Running"> Server did not return a status yet</br>'.format(
                STATIC_URL
            )
        elif status and "in_deploy" in status:
            response = '<img src="{}admin/img/icon-no.svg" alt="Not Running"> The server is deploying</br>'.format(
                STATIC_URL
            )
        elif status and "not_running" not in status:
            response = '<img src="{}admin/img/icon-yes.svg" alt="Running"> Server is running</br>'.format(
                STATIC_URL
            )
            try:
                content = loads(status.replace("'", '"'))
                for vehicle in content["vehicles"]:
                    vehicle_text = (
                        "[{}, Pit {}] {}: {} (SteamID:{}), penalties: {}".format(
                            vehicle["carClass"],
                            vehicle["pitGroup"],
                            vehicle["vehicleName"],
                            vehicle["driverName"],
                            vehicle["steamID"],
                            vehicle["penalties"],
                        )
                    )
                    response = response + vehicle_text + "</br>"
            except Exception as e:
                response = str(e)
        return mark_safe(response)

    def __str__(self):
        return self.url if not self.name else self.name

    def clean(self):
        status = self.status
        if not self.server_key and self.action:
            raise ValidationError(
                "The server was not processed yet. Wait a short time until the key is present."
            )
        if status is not None and "not_running" in status and self.action == "R-":
            raise ValidationError("The server is not running")

        if status is not None and "not_running" not in status and self.action == "D":
            raise ValidationError("Stop the server first")

        if status is not None and "not_running" not in status and self.action == "S+":
            raise ValidationError("Stop the server first")

        if self.action == "D" and not self.event:
            raise ValidationError("You have to add an event before deploying")

        if status and "in_deploy" in status:
            raise ValidationError("Wait until deployment is over")

        if self.action == "W" and status and "in_deploy" in status:
            raise ValidationError("Wait until deployment is over")

        if self.action == "W" and status and "not_running" in status:
            raise ValidationError("Start the server first")

        if status is not None and "not_running" not in status and self.action == "WU":
            raise ValidationError("Start the server first")

        if self.event and not self.event.real_weather and self.action == "WU":
            raise ValidationError("The event has no real weather enabled")

        if not str(self.url).endswith("/"):
            raise ValidationError("The server url must end with a slash!")

        other_servers = Server.objects.exclude(pk=self.pk)
        occupied_ports_tcp = []
        occupied_ports_udp = []

        from urllib.parse import urlparse

        server_url_parts = urlparse(self.url)
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

        if (
            self.http_port in occupied_ports_tcp
            or self.webui_port in occupied_ports_tcp
            or self.sim_port in occupied_ports_udp
        ):
            raise ValidationError(
                "The ports of this server are already taken. TCP ports taken: {}, UDP ports taken: {}".format(
                    occupied_ports_tcp, occupied_ports_tcp
                )
            )

        if MAX_SERVERS is not None:
            amount = Server.objects.count()
            if amount >= MAX_SERVERS:
                raise ValidationError(
                    "You exceeded the maximum amount of available servers. You are allowed to use {} server instances. You won't be able to deploy until you not exceed that limit anymore".format(
                        MAX_SERVERS
                    )
                )
        steamcmd_bandwidth = 0
        other_servers = Server.objects.all()
        for server in other_servers:
            if server.event:
                if self.pk != server.pk:
                    steamcmd_bandwidth = steamcmd_bandwidth + server.steamcmd_bandwidth

        steamcmd_bandwidth = steamcmd_bandwidth + self.steamcmd_bandwidth

        if MAX_STEAMCMD_BANDWIDTH is not None:
            if self.steamcmd_bandwidth == 0:
                raise ValidationError(
                    "Steamcmd bandwidth limits are enforced. Please set a limit for the steamcmd bandith. Available bandwidth: {} kbit/s".format(
                        MAX_STEAMCMD_BANDWIDTH - steamcmd_bandwidth
                    )
                )
            if steamcmd_bandwidth > MAX_STEAMCMD_BANDWIDTH:
                raise ValidationError(
                    "Steamcmd bandwidth limits are enforced. You exceeded the available bandwidth by {} kbit/s".format(
                        (MAX_STEAMCMD_BANDWIDTH - steamcmd_bandwidth) * -1
                    )
                )

        if self.event:
            upstream_sum = 0
            downstream_sum = 0
            other_servers = Server.objects.all()
            for server in other_servers:
                if server.event:
                    if self.pk != server.pk:
                        upstream_sum = upstream_sum + server.event.upstream
                        downstream_sum = downstream_sum + server.event.downstream

            upstream_sum = upstream_sum + self.event.upstream
            downstream_sum = downstream_sum + self.event.downstream
            if (
                MAX_DOWNSTREAM_BANDWIDTH is not None
                and MAX_DOWNSTREAM_BANDWIDTH <= downstream_sum
            ):
                raise ValidationError(
                    "You exceeded the maximum downstream bandwidth. You are allowed to use {} kbit/s, you requested {} kbit/s".format(
                        MAX_DOWNSTREAM_BANDWIDTH, downstream_sum
                    )
                )
            if (
                MAX_UPSTREAM_BANDWIDTH is not None
                and MAX_UPSTREAM_BANDWIDTH <= upstream_sum
            ):
                raise ValidationError(
                    "You exceeded the maximum upstream bandwidth. You are allowed to use {} kbit/s, you requested {} kbit/s".format(
                        MAX_UPSTREAM_BANDWIDTH, upstream_sum
                    )
                )
        if (
            self.action != ""
            or self.server_key is None
            or self.server_unlock_key is not None
        ):
            background_thread = Thread(
                target=background_action_server, args=(self,), daemon=True
            )
            background_thread.start()

        create_firewall_script(self)


def background_action_server(server):
    do_server_interaction(server)


@receiver(models.signals.pre_delete, sender=Server)
def remove_server_children(sender, instance, **kwargs):
    background_thread = Thread(
        target=remove_server_children_thread, args=(instance,), daemon=True
    )
    background_thread.start()


def remove_server_children_thread(instance):
    id = instance.public_secret
    server_children = join(BASE_DIR, "server_children", id)
    # lock the path to prevent the children management module to start stuff again
    lock_path = join(server_children, "delete.lock")
    with open(lock_path, "w") as file:
        file.write("bye")


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
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    message = models.TextField(
        blank=True,
        null=True,
        default=None,
        max_length=50,
        help_text="Submits a message or a command to the given server. Can't be longer than 50 chars",
    )
    success = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}@{}: {}".format(
            self.server, self.date.strftime("%m/%d/%Y, %H:%M:%S"), self.message
        )

    def clean(self):
        background_thread = Thread(
            target=background_action_chat, args=(self,), daemon=True
        )
        background_thread.start()


class ServerCron(models.Model):
    class Meta:
        verbose_name_plural = "Server schedules"
        verbose_name = "Server schedule"

    cron_text = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        default=None,
        help_text="Describe the execution time",
    )
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE, blank=False, null=False, default=None
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    last_execution = models.DateTimeField(blank=True, null=True, default=None)
    action = models.CharField(
        max_length=3,
        choices=ServerStatus.choices,
        blank=True,
        default="",
        help_text="Runs an activity on the server.",
        verbose_name="Pending action to submit",
    )
    message = models.TextField(
        default=None,
        null=True,
        blank=True,
        help_text="Message to send",
    )

    apply_only_if_practice = models.BooleanField(default=False)

    def __str__(self):
        return "{}: {}@{}".format(self.cron_text, self.action, self.server)

    def clean(self):
        if not croniter.is_valid(self.cron_text):
            raise ValidationError("This is not a valid cron description")
        if not self.server:
            raise ValidationError("Select a server first")
        if self.action == "D" and not self.event:
            raise ValidationError("You have to add an event before deploying")
        if self.message:
            parts = self.message.split(linesep)
            for part in parts:
                if len(part) > 50:
                    raise ValidationError(
                        "Limit the line length of each line of the text to 50!"
                    )


class TickerMessageType(models.TextChoices):
    PenaltyAdd = "P+", "PenaltyAdd"
    PenaltyRemove = "P-", "Penaltyrevoke"
    SlowCar = "V", "SlowCar"
    PitEntry = "PI", "PitEntry"
    PitExit = "PO", "PitExit"
    GarageEntry = "GI", "GarageEntry"
    GarageExit = "GO", "GarageExit"
    StatusChange = "S", "StatusChange"
    PositionChange = "P", "PositionChange"
    PositionChangeUnderYellow = "PY", "PositionChangeUnderYellow"
    BestLapChange = "PB", "BestLapChange"
    PitStatusChange = "PS", "PitStatusChange"
    Lag = "L", "Lag"
    LapsCompletedChange = "LC", "LapsCompletedChange"
    PittingStart = "PSS", "PittingStart"
    PittingEnd = "PSE", "PittingEnd"
    DriverSwap = "DS", "DriverSwap"
    VLow = "VL", "VLow"


class TickerMessage(models.Model):
    class Meta:
        verbose_name_plural = "Ticker messages"

    server = models.ForeignKey(
        Server, on_delete=models.CASCADE, blank=False, null=False, default=None
    )

    date = models.DateTimeField(auto_now_add=True)
    message = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        default=None,
        help_text="Event description",
    )

    type = models.CharField(
        max_length=3,
        choices=TickerMessageType.choices,
        blank=True,
        default="",
        help_text="Type",
        verbose_name="Type",
    )

    event_time = models.IntegerField(default=0)
    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="APX Session Id",
    )
    session = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="In game session identifier",
    )

    def __str__(self):
        try:
            data = loads(self.message)
            if self.type == "P+":
                return "Penalty added for {}".format(data["driver"])

            if self.type == "P-":
                return "Penalty revoked for {}".format(data["driver"])

            if self.type == "V":
                return "Slow car: {}".format(data["driver"])

            if self.type == "PI":
                return "Pit entry {}".format(data["driver"])

            if self.type == "PO":
                return "Pit exit {}".format(data["driver"])

            if self.type == "GI":
                return "Garage entry {}".format(data["driver"])

            if self.type == "GO":
                return "Garage exit {}".format(data["driver"])

            if self.type == "S":
                return "Status change {} (was: {} is: {})".format(
                    data["driver"], data["old_status"], data["status"]
                )

            if self.type == "P":
                return "New position for {}: P{} ({:+})".format(
                    data["driver"], data["new_pos"], data["new_pos"] - data["old_pos"]
                )

            if self.type == "PY":
                return "New position (possibly under yellow) for {}: P{} ({:+})".format(
                    data["driver"],
                    data["new_pos"],
                    data["new_pos"] - data["old_pos"],
                )

            if self.type == "PB":
                return "New personal best for {}: {}".format(
                    data["driver"], data["new_best"]
                )

            if self.type == "DS":
                return "Driver Swap: {} out, {} in".format(
                    data["old_driver"], data["new_driver"]
                )

            if self.type == "PS":
                return "Pit status change for {}: {} (was {})".format(
                    data["driver"], data["status"], data["old_status"]
                )

            if self.type == "LC":
                return "Driver {} now completed {} laps".format(
                    data["driver"], data["laps"]
                )

            if self.type == "PSS":
                return "Pitting start for {}".format(data["driver"])

            if self.type == "PSE":
                return "Pitting end for {}".format(data["driver"])

            if self.type == "L":
                return "Lag suspect for {}, nearby: {}. Speed difference was {}".format(
                    data["driver"],
                    "".join(data["nearby"]) if len(data["nearby"]) else "Nobody",
                    data["old_speed"] - data["speed"],
                )

            if self.type == "VL":
                return "Low speed or stationary car {}, nearby {}".format(
                    data["driver"], data["nearby"]
                )
        except Exception as e:
            print(e)
            pass
        return self.type