from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .forms import (
    SignupForm,
    EntryTokenForm,
    EntryFileForm,
    EntrySignupForm,
    EntryRevokeForm,
)
from wizard.settings import (
    USER_SIGNUP_ENABLED,
    USER_SIGNUP_RULE_TEXT,
    INSTANCE_NAME,
    MEDIA_ROOT,
)
from .models import EntryFile, Entry, Chat, Server, User
import pathlib
import zipfile
import tempfile
from os import listdir, mkdir
from os.path import join, basename
from django.core.files import File
from .util import get_hash, get_random_string, do_post, do_rc_post


def get_status(request, secret: str):
    server = Server.objects.filter(public_secret=secret).first()
    if not server:
        raise Http404()
    response = HttpResponse(server.status)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    response["Content-Type"] = "application/json"
    return response


def add_penalty(request, secret: str, driver: str, penalty: int, reason: str):
    server = Server.objects.get(public_secret=secret)
    if server is None:
        raise Http404()
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    if server is None:
        raise Http404()
    user = server.user
    message = ""
    description = ""
    if penalty != 19:
        if penalty == 1:  # DT
            message = "/addpenalty -1 {}".format(driver)
            description = "⚖️ DT penalty for {}."
        if penalty == 2:  # DQ
            message = "/dq {}".format(driver)
            description = "💀 {} is now disqualified."
        if penalty >= 3 and penalty <= 13:  # S&h 5 to 60
            length = 5 * (penalty - 1)
            message = "/addpenalty {} {}".format(length, driver)
            description = "🛑 " + str(length) + "s Stop and Hold penalty for {}"
        if penalty == 15:  # Remove one S&H
            message = "/subpenalty 0 {}".format(driver)
            description = "🚮 One Stop and Hold penalty was revoked for {}"
        if penalty == 16:  # Remove one DT
            message = "/subpenalty 1 {}".format(driver)
            description = "🚮 One DT penalty was revoked for {}"
        if penalty == 17:  # Remove all penalties
            description = "🚮 All assigned penalties removed for {}"
            message = "/subpenalty 3 {}".format(driver)
        if penalty == 18:  # UNDSQ
            description = "✔️ {} is now un-disqualified"
            message = "/undq {}".format(driver)
        if penalty >= 20 and penalty <= 30:  # add laps
            laps = penalty - 19
            description = "➕ Applied change of +" + str(laps) + " laps for {}"
            message = "/changelaps {} {}".format(laps, driver)
        if penalty >= 30 and penalty <= 40:  # add laps
            laps = penalty - 29
            description = "➖ Applied change of -" + str(laps) + " laps for {}"
            message = "/changelaps -{} {}".format(laps, driver)
        if message:
            chat = Chat()
            chat.server = server
            chat.message = message
            chat.user = user
            chat.save()
            response.write("ok")
            do_rc_post(description.format(driver))
            do_rc_post('👉 Reason by race control: "{}"'.format(reason))
            return response
        else:
            raise Http404()
    else:
        chat = Chat()
        chat.server = server
        chat.message = "/dq {}".format(driver)
        chat.user = user
        chat.save()
        chat = Chat()
        chat.server = server
        chat.message = "/undq {}".format(driver)
        chat.user = user
        chat.save()
        message = "✔️ Driver {} can now resume the race".format(driver)
        do_rc_post(description.format(driver))
        response.write("ok")
        return response


def get_team_revoke_form(request):
    if request.method == "POST":
        form = EntryRevokeForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get("token")
            results = Entry.objects.filter(token=token)
            if len(results) != 1:
                raise Http404()
            entry_string = str(results.first())
            results.delete()

            do_post(
                "[{}] 🚮 Team {} just revoked entry".format(INSTANCE_NAME, entry_string)
            )
            return render(
                request,
                "entry_revoke_confirm.html",
            )

    else:
        form = EntryRevokeForm()

    return render(
        request,
        "entry_revoke.html",
        {
            "form": form,
            "rules": USER_SIGNUP_RULE_TEXT,
            "instance_name": INSTANCE_NAME,
        },
    )


def get_team_signup_form(request, client: str):
    if request.method == "POST":
        form = EntrySignupForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data.get("number")
            team_name = form.cleaned_data.get("team_name")
            client = form.cleaned_data.get("client")
            component = form.cleaned_data.get("component")

            client_obj = None
            users = User.objects.all()
            for user in users:
                needle = get_hash(str(user.pk))
                if client == needle:
                    client_obj = user
                    break
            if not client:
                raise ValidationError("Invalid client")

            token = get_random_string(10)
            new_entry = Entry()
            new_entry.user = client_obj
            new_entry.component = component
            new_entry.team_name = team_name
            new_entry.vehicle_number = int(number)
            new_entry.token = token
            new_entry.save()
            entry_string = str(new_entry)
            do_post("[{}] 👋 Team {} just signed up".format(INSTANCE_NAME, entry_string))
            return render(
                request,
                "entry_signup_confirm.html",
                {"instance_name": INSTANCE_NAME, "token": token, "entry": new_entry},
            )

    else:
        form = EntrySignupForm()
        form.fields["client"].initial = client
    return render(
        request,
        "entry_signup.html",
        {
            "form": form,
            "rules": USER_SIGNUP_RULE_TEXT,
            "instance_name": INSTANCE_NAME,
            "client": client,
        },
    )


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
                    needs_secondary_save = False
                    full_path = join(temp_extract_path, file)
                    entry_file = EntryFile()
                    entry_file.entry = entry
                    entry_file.user = entry.user

                    needle = "{}_{}".format(
                        entry.component.short_name, entry.vehicle_number
                    )

                    needs_secondary_save = full_path.endswith(
                        needle + ".dds"
                    ) or full_path.endswith(needle + "_Region.dds")

                    with open(full_path, "rb") as livery_file:
                        entry_file.file.save(file, File(livery_file), save=True)
                    entry_file.save()

                    results[file] = basename(entry_file.file.name)
                    # A secondary safe just triggers save() again to add numberplates, if needed.
                    # For files not required to have numberplate element, it's just a seconds save() call
                    if needs_secondary_save:
                        results[
                            file + " (numberplates)"
                        ] = "Applied numberplate #{}".format(entry.vehicle_number)
                        entry_file.save()
                entry_string = str(entry)
                do_post(
                    "[{}] 🎨 Team {} just added a livery ({})".format(
                        INSTANCE_NAME, entry_string, ", ".join(results.values())
                    )
                )
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
            # create directories
            id = get_hash(str(new_user.id))
            paths = [
                join(MEDIA_ROOT, "logs", id),
                join(MEDIA_ROOT, "keys", id),
                join(
                    MEDIA_ROOT,
                    id,
                ),
                join(MEDIA_ROOT, id, "conditions"),
                join(MEDIA_ROOT, id, "liveries"),
                join(MEDIA_ROOT, id, "templates"),
            ]
            for path in paths:
                mkdir(path)
            do_post(
                "[{}]: 😁 A new user signed up: {} ({})".format(
                    INSTANCE_NAME, user, email
                )
            )
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
