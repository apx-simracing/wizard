from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .forms import SignupForm
from wizard.settings import USER_SIGNUP_ENABLED


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
            if password != password_repeat:
                raise ValidationError("The passwords do not match")

            result = User.objects.filter(Q(username=user) | Q(email=email))

            if result.count() > 0:
                raise ValidationError("User or email already taken")

            if not rules_accept:
                raise ValidationError("You have to accept the rules")

            new_user = User(username=user, email=email, is_staff=True, is_active=True)
            new_user.set_password(password)

            new_user.save()
            group = Group.objects.get(name="Users")
            new_user.groups.add(group)
            new_user.save()

            return HttpResponse("You can now login on the backend")
    else:
        form = SignupForm()

    return render(request, "signup.html", {"form": form})
