from django.db import models
from django.core.exceptions import ValidationError
from django import forms
from django.dispatch import receiver
from os.path import isfile
from os import remove
from webgui.util import livery_filename


class ComponentType(models.TextChoices):
    VEHICLE = "VEH", "Vehicle"
    LOCATION = "LOC", "Location"


class Component(models.Model):
    type = models.CharField(
        max_length=3, choices=ComponentType.choices, default=ComponentType.VEHICLE
    )
    steam_id = models.IntegerField(default=0, blank=True)
    component_version = models.CharField(
        default="1.0",
        max_length=20,
        help_text="The version to use. You can use 'latest' or 'latest-even' to either get the latest or the latest even version.",
    )
    component_name = models.CharField(default="Example_Mod", max_length=200)
    do_update = models.BooleanField(
        default=False, help_text="If you plan to add liveries on a car, check this."
    )
    short_name = models.CharField(
        default="",
        max_length=200,
        help_text="The short name is required to idenitfy (livery) filenames belonging to this component. You only need this when 'Do update' is checked.",
    )

    def __str__(self):
        return "{} ({})".format(self.component_name, self.component_version)


class RaceConditions(models.Model):
    description = models.TextField(default="Add description")
    rfm = models.FileField()

    def __str__(self):
        return "{} ({})".format(self.description, self.rfm)


class Track(models.Model):
    component = models.ForeignKey(Component, on_delete=models.DO_NOTHING)
    layout = models.CharField(default="", blank=False, max_length=200)

    def __str__(self):
        return "{}@{}".format(self.layout, self.component)


class Entry(models.Model):
    component = models.ForeignKey(Component, on_delete=models.DO_NOTHING)
    team_name = models.CharField(default="Example Team", max_length=200)
    vehicle_number = models.IntegerField(default=1)

    def __str__(self):
        return "{}#{} ({})".format(self.team_name, self.vehicle_number, self.component)


class EntryFile(models.Model):
    file = models.FileField(upload_to=livery_filename)
    entry = models.ForeignKey(
        Entry, on_delete=models.DO_NOTHING, blank=False, null=False, default=None
    )

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

    def __str__(self):
        return "{}".format(self.name)


class ServerStatus(models.TextChoices):
    STARTREQUESTED = "S+", "Start"
    STOPREQUESTED = "R-", "Stop"
    DEPLOY = "D", "Change config"
    UPDATELIVERIES = "U", "Update liveries and redeploy"


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
        help_text="Runs an activity on the server. 'Change config' and 'pdate liveries and redeploy' require the server to be not running.",
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
    )

    def __str__(self):
        return self.url if not self.name else self.name
