"""
Django settings for wizard project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ")fja6coe&-2ixc#9&swb3)x2@dg8jr$-vf#za@*q07ma-ba4@v"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "frontend_cache",
    }
}

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

STATIC_URL = "/static/"

MEDIA_URL = "http://localhost:8000/"

PUBLIC_URL = "http://localhost:8000/"

FAILURE_THRESHOLD = 500

MEDIA_URL = "http://localhost:8181/"

from os.path import join

MEDIA_ROOT = join(str(BASE_DIR), "uploads")

APX_ROOT = "C:\\Users\\chm\\Documents\\rfactor-server\\cli"

PACKS_ROOT = join(str(BASE_DIR), "packs")

USER_SIGNUP_ENABLED = False

USER_SIGNUP_RULE_TEXT = ""

INSTANCE_NAME = "APX Wizard"

ENTRY_SIGNUP_ENABLED = False

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/809457280541524018/p0qconwiP0avBpHqCX-PN4TQH-hNimdc7dxx5Et4rQc6m5r2M4NCDjxOQnB2aqUoVsyJ"

DISCORD_WEBHOOK_NAME = "detlev"

DISCORD_RACE_CONTROL_WEBHOOK = None

DISCORD_RACE_CONTROL_WEBHOOK_NAME = "APX Race Control"

OPENWEATHERAPI_KEY = "8c02a746038985d141962b8c16d5a237"

CRON_CHUNK_SIZE = 1

CRON_THREAD_KILL_TIMEOUT = 20

CRON_TIMEOUT = 1

CRON_TIMEZONE = "Europe/Berlin"
