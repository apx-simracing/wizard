from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .forms import SignupForm
from wizard.settings import USER_SIGNUP_ENABLED, USER_SIGNUP_RULE_TEXT, INSTANCE_NAME


def get_rules_page(request):
    if not USER_SIGNUP_ENABLED:
        raise Http404("Signup not enabled on this instance.")
    return render(
        request,
        "rules.html",
        {"rules": USER_SIGNUP_RULE_TEXT, "instance_name": INSTANCE_NAME},
    )


def get_signup_form(request):
    if not USER_SIGNUP_ENABLED:
        raise Http404("Signup not enabled on this instance.")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            password_repeat = form.cleaned_data.get("password_repeat")
            rules_accept = form.cleaned_data.get("rules_accept")

            new_user = User(username=user, email=email, is_staff=True, is_active=True)
            new_user.set_password(password)

            new_user.save()
            group = Group.objects.get(name="Users")
            new_user.groups.add(group)
            new_user.save()

            return render(
                request,
                "signup_success.html",
            )

    else:
        form = SignupForm()

    return render(
        request,
        "signup.html",
        {"form": form, "rules": USER_SIGNUP_RULE_TEXT, "instance_name": INSTANCE_NAME},
    )
