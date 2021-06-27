from django.http import HttpResponse, Http404, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
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
    MEDIA_URL,
)
from .models import (
    EntryFile,
    Entry,
    Chat,
    Server,
    User,
    Event,
    Component,
    TickerMessage,
    ServerStatustext,
)
import pathlib
import zipfile
import tempfile
from json import loads, dumps
from django.core import serializers
from os import listdir, mkdir, unlink
from os.path import join, basename, exists
from django.core.files import File
from .util import (
    get_hash,
    get_random_string,
    do_post,
    do_rc_post,
    get_server_hash,
    run_apx_command,
)
from django.views.decorators.csrf import csrf_exempt
import tarfile
from math import floor, ceil


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
            new_entry.user = event_obj.user
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


def get_entry_signup_form(request, entry: int):
    pass


from datetime import date
from collections import OrderedDict


def get_ticker(request, secret: str):
    server = Server.objects.get(public_secret=secret)

    messages = TickerMessage.objects.filter(server__public_secret=secret)

    session_id = server.session_id

    last_status = (
        ServerStatustext.objects.filter(server=server, session_id=session_id)
        .order_by("-id")
        .first()
    )
    vehicles = {}
    raw_status = loads(last_status.status.replace("'", '"')) if last_status else None
    if raw_status:
        for vehicle in raw_status["vehicles"]:
            position = vehicle["position"]
            vehicles[position] = vehicle
    vehicles = OrderedDict(sorted(vehicles.items()))
    return render(
        request,
        "ticker.html",
        {"messages": messages, "status": raw_status, "vehicles": vehicles},
    )


def get_weather(request, secret: str):
    server = Server.objects.filter(public_secret=secret).first()
    if not server or not server.event or not server.event.real_weather:
        raise Http404()
    unlocked = False
    if "secret" in request.GET:
        print(server.secret)
        unlocked = server.secret == request.GET["secret"]
    sessions = server.event.conditions.sessions.all()

    forecast = {}
    for session in sessions:
        start = session.start
        if start:
            lines = session.weather.splitlines()
            blocks = []
            current_block = None
            for line in lines:
                if "StartTime" in line:
                    if current_block is not None:
                        blocks.append(current_block)
                    current_block = {}
                if "//" not in line:
                    parts = line.split("=")
                    raw = int(parts[1].replace("(", "").replace(")", ""))
                    if "StartTime" in line:
                        humanTime = ""
                        hours = floor(raw / 60)
                        minutes = raw % 60
                        if len(str(hours)) == 1:
                            humanTime = humanTime + "0" + str(hours)
                        else:
                            if hours == 24:
                                humanTime = humanTime + "00"
                            else:
                                humanTime = humanTime + str(hours)

                        if len(str(minutes)) == 1:
                            humanTime = humanTime + ":0" + str(minutes)
                        else:
                            humanTime = humanTime + ":" + str(minutes)
                        current_block["HumanTime"] = humanTime

                    current_block[parts[0]] = raw
                if "//POP=" in line and current_block:
                    current_block["Probability"] = line.replace("//POP=", "")
                if "//SERVERPOP=" in line and current_block:
                    current_block["MatchedProbability"] = line.replace(
                        "//SERVERPOP=", ""
                    )

            if session.length:
                # session has a length
                # get all blocks for the session
                block_length = 0
                for block in blocks:
                    if block_length > session.length:
                        break
                    if session.id not in forecast:
                        forecast[session.id] = []
                    forecast[session.id].append(block)
                    block_length = block_length + block["Duration"]
            else:
                for block in blocks:
                    if session.id not in forecast:
                        forecast[session.id] = []
                    forecast[session.id].append(block)
    return render(
        request,
        "forecast.html",
        {
            "unlocked": unlocked,
            "event": server.event,
            "sessions": sessions,
            "forecast": forecast,
        },
    )


@csrf_exempt
def add_message(request, secret: str):
    server = Server.objects.filter(public_secret=secret).first()
    if not server:
        raise Http404()

    data = request.body.decode("utf-8")
    parsed = loads(data)
    ticker = TickerMessage()
    ticker.message = data
    ticker.type = parsed["type"]
    ticker.event_time = parsed["event_time"]
    ticker.session = parsed["session"]
    ticker.server = server
    ticker.user = server.user
    ticker.session_id = server.session_id
    ticker.save()
    return JsonResponse({})


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

    text = ServerStatustext()
    try:
        parsed_text = loads(got)
        if "session_id" in parsed_text and parsed_text["session_id"] is not None:
            old_id = server.session_id
            server.session_id = parsed_text["session_id"]
            text.session_id = server.session_id
    except:
        pass
    text.user = server.user
    text.server = server
    text.status = got
    text.save()
    server.save()
    return HttpResponse("OK")


@csrf_exempt
def live(request, secret: str):
    server = Server.objects.filter(public_secret=secret).first()

    if not server:
        raise Http404()
    session_id = server.session_id
    url = server.url
    key = get_server_hash(url)

    status = loads(
        ServerStatustext.objects.filter(server=server, session_id=session_id)
        .order_by("id")
        .last()
        .status
    )
    raw_messages = (
        TickerMessage.objects.filter(server=server)
        .filter(session_id=server.session_id)
        .filter(session=status["session"])
        .order_by("id")
    )
    messages = {}
    drivers = {}
    for message in raw_messages:
        message_content = loads(message.message)
        slot_id = message_content["slot_id"]
        if slot_id not in messages:
            messages[slot_id] = []
        messages[slot_id].append(message_content)
        if message.type == "DS":
            old_driver = message_content["old_driver"]
            new_driver = message_content["new_driver"]
            if slot_id not in drivers:
                drivers[slot_id] = []

            if old_driver not in drivers[slot_id]:
                drivers[slot_id].append(old_driver)
            if new_driver not in drivers[slot_id]:
                drivers[slot_id].append(new_driver)

    status["vehicles"] = sorted(status["vehicles"], key=lambda x: x["position"])
    status["ticker_classes"] = (
        loads(server.event.timing_classes) if server.event else {}
    )
    # create in-class positions
    class_cars = {}
    for vehicle in status["vehicles"]:
        if vehicle["carClass"] not in class_cars:
            class_cars[vehicle["carClass"]] = 0
        class_cars[vehicle["carClass"]] = class_cars[vehicle["carClass"]] + 1
        vehicle["classPosition"] = class_cars[vehicle["carClass"]]
        vehicle["messages"] = (
            messages[vehicle["slotID"]] if vehicle["slotID"] in messages else []
        )
        vehicle["messages"].reverse()

    # get ticker messages
    ticker = []
    ticker_messages_raw = raw_messages.filter(type="VL")
    current_time = status["currentEventTime"]
    # we have only vlow atm
    for message in ticker_messages_raw:
        message_content = loads(message.message)
        driver = message_content["driver"]
        laps = message_content["laps"]
        event_time = message_content["event_time"]

        location = message_content["location"]
        # remove duplicate hits if the car remains staionary
        matches = list(
            filter(
                lambda x: x["driver"] == driver
                and x["laps"] == laps
                and (
                    x["location"] >= location - 100 and x["location"] <= location + 100
                ),
                ticker,
            )
        )
        if event_time >= current_time - 20 and not len(matches) > 0:
            ticker.append(message_content)

    response = {
        "status": status,
        "media_url": MEDIA_URL,
        "drivers": drivers,
        "ticker": ticker,
    }

    return JsonResponse(response)