from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.conf import settings
from django import forms
from django.dispatch import receiver
from os.path import isfile
from os import remove
from json import loads
from django.core.validators import RegexValidator
from webgui.util import (
    livery_filename,
    run_apx_command,
    get_server_hash,
    get_key_root_path,
    get_conditions_file_root,
    get_update_filename,
)
from wizard.settings import FAILURE_THRESHOLD
from webgui.storage import OverwriteStorage


class ComponentType(models.TextChoices):
    VEHICLE = "VEH", "Vehicle"
    LOCATION = "LOC", "Location"


alphanumeric_validator = RegexValidator(
    r"^[0-9a-zA-Z_]*$", "Only alphanumeric characters and dashes are allowed."
)


class Component(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=3, choices=ComponentType.choices, default=ComponentType.VEHICLE
    )
    steam_id = models.IntegerField(default=0, blank=True)
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

    def clean(self):
        if self.type != ComponentType.VEHICLE and self.do_update:
            raise ValidationError(
                "Only vehicle components can currently recieve updates (for liveries)"
            )
        if self.type != ComponentType.VEHICLE and self.update:
            raise ValidationError("Only vehicle components can get an Update.ini file")

    def __str__(self):
        return "{} ({})".format(self.component_name, self.component_version)


class RaceConditions(models.Model):
    class Meta:
        verbose_name_plural = "Race conditions"

    description = models.TextField(default="Add description")
    rfm = models.FileField(upload_to=get_conditions_file_root, storage=OverwriteStorage)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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
    vehicle_number = models.IntegerField(default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return "{}#{} ({})".format(self.team_name, self.vehicle_number, self.component)


class EntryFile(models.Model):
    file = models.FileField(upload_to=livery_filename, storage=OverwriteStorage)
    entry = models.ForeignKey(
        Entry, on_delete=models.DO_NOTHING, blank=False, null=False, default=None
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.entry)


@receiver(models.signals.post_delete, sender=EntryFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.file:
        if isfile(instance.file.path):
            remove(instance.file.path)


class Event(models.Model):
    overwrites_multiplayer = models.TextField(default="{}")
    overwrites_player = models.TextField(default="{}")
    name = models.CharField(default="", max_length=200)
    conditions = models.ForeignKey(RaceConditions, on_delete=models.DO_NOTHING)
    entries = models.ManyToManyField(Entry)
    tracks = models.ManyToManyField(Track)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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
        verbose_name="Processing",
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status_failures = models.IntegerField(
        default=0,
        help_text="The amount of failed status checks. The field will reset on save. If more than {} attemps will fail, the server will be ignored for status and actions..".format(
            FAILURE_THRESHOLD
        ),
    )

    def __str__(self):
        return self.url if not self.name else self.name

    def clean(self):
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

        if self.action == "D" and not self.event:
            raise ValidationError("You have to add an event before deploying")

        self.status_failures = 0


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

    def save(self, *args, **kwargs):
        try:
            key = get_server_hash(self.server.url)
            run_apx_command(key, "--cmd chat --args {} ".format(self.message))
            self.success = True
        except:
            self.success = False
            pass

        super(Chat, self).save(*args, **kwargs)


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