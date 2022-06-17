"""
Django settings for wizard project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
from os.path import join

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "DEMO"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "webgui.apps.WebguiConfig",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

FILE_UPLOAD_HANDLERS = ("django.core.files.uploadhandler.TemporaryFileUploadHandler",)

ROOT_URLCONF = "wizard.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "wizard.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",        
        "OPTIONS": {
            "timeout": 10,
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

WIZARD_PORT = 8000

LISTEN_IP = "127.0.0.1"

STATIC_PORT = 8383

STATIC_ROOT = join(str(BASE_DIR), "static")

STATIC_URL = f"http://localhost:{STATIC_PORT}/"

LIBRARY_PATH = None

MEDIA_PORT = 8282

MEDIA_URL = f"http://localhost:{MEDIA_PORT}/"

PUBLIC_URL = f"http://localhost:{WIZARD_PORT}/"

FAILURE_THRESHOLD = 500

MEDIA_ROOT = join(str(BASE_DIR), "uploads")

APX_ROOT = join(str(BASE_DIR), "cli")

PACKS_ROOT = join(str(BASE_DIR), "packs")

DISCORD_WEBHOOK = None

DISCORD_WEBHOOK_NAME = None

DISCORD_RACE_CONTROL_WEBHOOK = None

DISCORD_RACE_CONTROL_WEBHOOK_NAME = "APX Race Control"

OPENWEATHERAPI_KEY = ""

MAX_SERVERS = None

MAX_STEAMCMD_BANDWIDTH = None

MAX_UPSTREAM_BANDWIDTH = None

MAX_DOWNSTREAM_BANDWIDTH = None

RECIEVER_PORT_RANGE = [5000, 10000]

WEBUI_PORT_RANGE = [10001, 35000]

HTTP_PORT_RANGE = [35001, 55000]

SIM_PORT_RANGE = [55001, 65000]

MSG_LOGO = "https://apx.chmr.eu/images/apx.png"

USE_GLOBAL_STEAMCMD = False

EASY_MODE = True

ADD_PREFIX = True

SPEEDTEST_ALLOWED = True

NON_WORKSHOP_PAYLOAD_TEXT = "Contact administrator for source"

WINE_DRIVE = "Z"

WINE_IMPLEMENTATION = "wine"