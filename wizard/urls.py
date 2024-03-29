"""wizard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from webgui.views import (
    get_signup_form,
    get_rules_page,
    get_token_form,
    get_files_form,
    get_team_signup_form,
    get_team_revoke_form,
    add_penalty,
    get_status,
    get_ticker,
    add_message,
    add_status,
    add_log,
    get_weather,
    live,
    index_view,
)
from wizard.settings import ENTRY_SIGNUP_ENABLED

if ENTRY_SIGNUP_ENABLED:
    urlpatterns = [
        path("", index_view),
        path("admin/", admin.site.urls),
        path("signup/", get_signup_form),
        path("rules/", get_rules_page),
        path("entry/", get_token_form),
        path("files/", get_files_form),
        path("team/<event>", get_team_signup_form),
        path("revoke/", get_team_revoke_form),
        path(
            "penalty/<str:secret>/<str:driver>/<int:penalty>/<str:reason>", add_penalty
        ),
        path("status/<str:secret>", get_status),
        path("ticker/<str:secret>", get_ticker),
        path("addmessage/<str:secret>", add_message),
        path("addstatus/<str:secret>", add_status),
        path("addlog/<str:secret>", add_log),
        path("live/<str:secret>", live),
        path("weather/<str:secret>", get_weather),
    ]
else:
    urlpatterns = [
        path("", index_view),
        path("admin/", admin.site.urls),
        path("signup/", get_signup_form),
        path("rules/", get_rules_page),
        path(
            "penalty/<str:secret>/<str:driver>/<int:penalty>/<str:reason>", add_penalty
        ),
        path("status/<str:secret>", get_status),
        path("ticker/<str:secret>", get_ticker),
        path("addmessage/<str:secret>", add_message),
        path("addstatus/<str:secret>", add_status),
        path("addlog/<str:secret>", add_log),
        path("live/<str:secret>", live),
        path("weather/<str:secret>", get_weather),
    ]