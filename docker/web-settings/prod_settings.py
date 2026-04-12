"""
Docker-oriented Django settings for CTF Gameserver web.
"""

import os

from ctf_gameserver.web.base_settings import *  # noqa: F403,F401


CSP_POLICIES = {
    'base-uri': ["'self'"],
    'connect-src': ["'self'"],
    'form-action': ["'self'"],
    'object-src': ["'none'"],
    'script-src': ["'self'"],
    'style-src': ["'self'"],
}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('CTF_DBHOST', 'db'),
        'PORT': os.environ.get('CTF_DBPORT', ''),
        'NAME': os.environ.get('CTF_DBNAME', 'ctf_gameserver'),
        'USER': os.environ.get('CTF_DBUSER', 'ctf_gameserver'),
        'PASSWORD': os.environ.get('CTF_DBPASSWORD', 'ctf_gameserver'),
        'CONN_MAX_AGE': 60,
    }
}

# Keep cache requirements minimal for compose deployments.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'ctf-gameserver.web@localhost')

MEDIA_ROOT = os.environ.get('CTF_MEDIA_ROOT', '/data/uploads')
TEAM_DOWNLOADS_ROOT = os.environ.get('CTF_TEAM_DOWNLOADS_ROOT', '/data/team_downloads')
STATIC_ROOT = os.environ.get('CTF_STATIC_ROOT', '/data/static')

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-before-production')
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        'http://localhost:8000,http://127.0.0.1:8000'
    ).split(',') if o.strip()
]
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')
FIRST_DAY_OF_WEEK = int(os.environ.get('DJANGO_FIRST_DAY_OF_WEEK', '1'))

DEBUG = os.environ.get('DJANGO_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')
