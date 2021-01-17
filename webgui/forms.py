from django import forms


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=100)
    username = forms.CharField(label="Username", max_length=100)
    password = forms.CharField(label="Password", widget=forms.PasswordInput())
    password_repeat = forms.CharField(
        label="Repeat password", widget=forms.PasswordInput()
    )
    rules_accept = forms.BooleanField(label="I accept the rules")
