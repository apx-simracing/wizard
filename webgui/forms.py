from django import forms
from webgui.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q


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
