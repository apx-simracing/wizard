from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .forms import SignupForm, EntryTokenForm, EntryFileForm
from wizard.settings import USER_SIGNUP_ENABLED, USER_SIGNUP_RULE_TEXT, INSTANCE_NAME
from .models import EntryFile, Entry
import pathlib
import zipfile
import tempfile
from os import listdir
from os.path import join, basename
from django.core.files import File


def get_rules_page(request):
    if not USER_SIGNUP_ENABLED:
        raise Http404("Signup not enabled on this instance.")
    return render(
        request,
        "rules.html",
        {"rules": USER_SIGNUP_RULE_TEXT, "instance_name": INSTANCE_NAME},
    )


def get_token_form(request):
    if request.method == "POST":
        form = EntryTokenForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get("token")
            entry = Entry.objects.get(token=token)
            files = EntryFile.objects.filter(entry__token=token)
            form = EntryFileForm()
            form.fields["token"].initial = token
            return render(
                request,
                "entry_files.html",
                {"token": token, "entry_files": files, "entry": entry, "form": form},
            )

    else:
        form = EntryTokenForm()

    return render(
        request,
        "entry_token.html",
        {"form": form, "rules": USER_SIGNUP_RULE_TEXT, "instance_name": INSTANCE_NAME},
    )


def get_files_form(request):
    if request.method == "POST":
        form = EntryFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data.get("file")
            token = form.cleaned_data.get("token")
            temp_path = file.temporary_file_path()
            temp_extract_path = tempfile.mkdtemp(prefix="apx")

            with zipfile.ZipFile(temp_path, "r") as zip_obj:
                zip_obj.extractall(temp_extract_path)

            files = listdir(temp_extract_path)
            entry = Entry.objects.filter(token=token).first()

            if entry:
                results = {}
                EntryFile.objects.filter(entry__token=token).delete()
                for file in files:
                    full_path = join(temp_extract_path, file)
                    entry_file = EntryFile()
                    entry_file.entry = entry
                    entry_file.user = entry.user
                    with open(full_path, "rb") as livery_file:
                        entry_file.file.save(file, File(livery_file), save=True)
                    entry.save()
                    results[file] = basename(entry_file.file.name)

                return render(
                    request, "files_updated.html", {"files": results, "entry": entry}
                )
            else:
                raise Http404("Not found")
        else:
            raise Http404("Not found")
    else:
        raise Http404("Not found")


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
