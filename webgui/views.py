import tempfile
import zipfile
from json import loads
from os import listdir, mkdir, unlink
from os.path import exists, join

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from wizard.settings import (INSTANCE_NAME, MEDIA_ROOT, MEDIA_URL,
                             USER_SIGNUP_ENABLED, USER_SIGNUP_RULE_TEXT)

from .forms import (EntryFileForm, EntryRevokeForm, EntrySignupForm,
                    EntryTokenForm, SignupForm)
from .models import Entry, EntryFile, Event, Server, User, status_map
from .util import (FILE_NAME_SUFFIXES, FILE_NAME_SUFFIXES_MEANINGS, do_post,
                   get_hash, get_random_string, get_server_hash)


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


def get_team_signup_form(request, event: int):
    event_obj = Event.objects.filter(pk=event, signup_active=True).first()
    if not event_obj:
        raise Http404("No suitable event found")

    if request.method == "POST":
        form = EntrySignupForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data.get("number")
            team_name = form.cleaned_data.get("team_name")
            component = form.cleaned_data.get("component")

            if not event_obj:
                raise ValidationError("Event")

            token = get_random_string(10)
            new_entry = Entry()
            new_entry.component = component
            new_entry.team_name = team_name
            new_entry.vehicle_number = int(number)
            new_entry.token = token
            new_entry.save()

            # add new entry to event
            event_obj.entries.add(new_entry)
            entry_string = str(new_entry)
            do_post(
                "[{}] 👋 Team {} just signed for {} up".format(
                    INSTANCE_NAME, entry_string, event_obj.name
                )
            )
            return render(
                request,
                "entry_signup_confirm.html",
                {"instance_name": INSTANCE_NAME, "token": token, "entry": new_entry},
            )

    else:
        form = EntrySignupForm()
        # events gets added for validation purposes
        form.fields["component"].queryset = event_obj.signup_components
        form.fields["event"].initial = event
    return render(
        request,
        "entry_signup.html",
        {
            "event": event,
            "form": form,
            "rules": USER_SIGNUP_RULE_TEXT,
            "instance_name": INSTANCE_NAME,
            "event_obj": event_obj,
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

                    needle = "{}_{}".format(
                        entry.component.short_name, entry.vehicle_number
                    )

                    needs_secondary_save = full_path.endswith(
                        needle + ".dds"
                    ) or full_path.lower().endswith(needle + "_region.dds")
                    file_name = None
                    suffix_meaning = None
                    for index, suffix in enumerate(FILE_NAME_SUFFIXES):
                        if suffix.lower() in file:
                            file_name = needle + suffix
                            suffix_meaning = FILE_NAME_SUFFIXES_MEANINGS[index]

                    with open(full_path, "rb") as livery_file:
                        entry_file.file.save(file_name, File(livery_file), save=True)
                    entry_file.save()

                    results[file] = suffix_meaning
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


def get_entry_signup_form(request, entry: int):
    pass


@csrf_exempt
def add_log(request, secret: str):
    server = Server.objects.filter(secret=secret).first()
    if not server:
        raise Http404()

    url = server.url
    key = get_server_hash(url)

    if "log" in request.FILES:
        file = request.FILES["log"]
        absolute_path = join(MEDIA_ROOT, "logs", key)
        if not exists(absolute_path):
            mkdir(absolute_path)

        absolute_log_path = join(MEDIA_ROOT, "logs", key, "reciever.log")
        if exists(absolute_log_path):
            unlink(absolute_log_path)
        path = join("logs", key, "reciever.log")
        default_storage.save(path, ContentFile(file.read()))
        return HttpResponse()
    else:
        raise HttpResponseBadRequest()


@csrf_exempt
def add_status(request, secret: str):
    server = Server.objects.filter(secret=secret).first()
    if not server:
        raise Http404()
    got = request.body.decode("utf-8")
    try:
        parsed_text = loads(got)
        if "session_id" in parsed_text and parsed_text["session_id"] is not None:
            old_id = server.session_id
            server.session_id = parsed_text["session_id"]
    except:
        pass
    status_map[server.pk] = got
    return HttpResponse("OK")


def index_view(request):
    return redirect("/admin")
