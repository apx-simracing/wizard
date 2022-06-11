from json import loads
from os import mkdir, unlink
from os.path import exists, join

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from wizard.settings import MEDIA_ROOT

from .models import Server, status_map
from .util import get_server_hash



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
    parsed_text = None
    try:
        parsed_text = loads(got)
        if "session_id" in parsed_text and parsed_text["session_id"] is not None:
            server.session_id = parsed_text["session_id"]
    except:
        pass
    status_map[server.pk] = parsed_text
    return HttpResponse("OK")


def index_view(request):
    return redirect("/admin")
