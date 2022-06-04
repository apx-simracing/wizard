from django import forms
from webgui.models import User, Entry, Component, Event
from django.core.exceptions import ValidationError
from django.db.models import Q
import os


class EntryRevokeForm(forms.Form):
    token = forms.CharField(
        label="Token",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )


class EntrySignupForm(forms.Form):
    component = forms.ModelChoiceField(
        queryset=Component.objects.all(),
    )
    number = forms.IntegerField()
    team_name = forms.CharField()
    event = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        event_id = self.cleaned_data.get("event")
        event_obj = Event.objects.filter(pk=event_id, signup_active=True).first()
        number = self.cleaned_data.get("number")

        if not event_obj:
            raise ValidationError("Invalid Event")

        matching_numbers = Entry.objects.filter(vehicle_number=number)

        if len(matching_numbers) != 0:
            raise ValidationError("Number already taken")


class EntryTokenForm(forms.Form):
    token = forms.CharField(
        label="Token",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )

    def clean(self):
        token = self.cleaned_data.get("token")
        result = Entry.objects.filter(token=token)

        if result.count() == 0:
            raise ValidationError("This token is unknown!")


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".zip"]
    if not ext.lower() in valid_extensions:
        raise ValidationError("Unsupported file extension.")


class EntryFileForm(forms.Form):
    token = forms.CharField(
        label="Token",
        max_length=100,
        widget=forms.HiddenInput(),
    )
    file = forms.FileField(
        validators=[validate_file_extension], widget=forms.ClearableFileInput()
    )


class SignupForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    username = forms.CharField(
        label="Username",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(attrs={"class": "form-input"})
    )
    password_repeat = forms.CharField(
        label="Repeat password",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
    rules_accept = forms.BooleanField(
        label="I accept the rules",
        widget=forms.CheckboxInput(attrs={"class": "form-input"}),
        initial=False,
    )

    def clean(self):
        user = self.cleaned_data.get("username")
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")
        password_repeat = self.cleaned_data.get("password_repeat")
        rules_accept = self.cleaned_data.get("rules_accept")
        if password != password_repeat:
            raise ValidationError("The passwords do not match")

        result = User.objects.filter(Q(username=user) | Q(email=email))

        if result.count() > 0:
            raise ValidationError("User or email already taken")

        if not rules_accept:
            raise ValidationError("You have to accept the rules")
