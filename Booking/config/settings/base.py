# ruff: noqa: ERA001, E501
"""Base settings to build other settings files upon."""
import os
from pathlib import Path
import environ
import mimetypes

# Initialisation des types MIME pour les polices
mimetypes.add_type("application/font-woff", ".woff")
mimetypes.add_type("application/font-woff2", ".woff2")
mimetypes.add_type("application/x-font-ttf", ".ttf")
mimetypes.add_type("application/x-font-otf", ".otf")

# Configuration de l'environnement
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = BASE_DIR / "booking"
env = environ.Env()
env.read_env(str(BASE_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", False)
TIME_ZONE = "UTC"
LANGUAGE_CODE = "fr-fr"  # Changé en français pour correspondre à votre application
SITE_ID = 1
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [str(BASE_DIR / "locale")]

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "assienian_db",
        "USER": "postgres",
        "PASSWORD": env("DB_PASSWORD", default="ella"),
        "HOST": "localhost",
        "PORT": "5432",
    }
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.forms",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "fontawesomefree",
    "widget_tweaks",
    "django_ckeditor_5",
]

LOCAL_APPS = [
    "rest_framework",
    "booking.users",
    "backoffice",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {"sites": "booking.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "pages:dashboard"
LOGIN_URL = "account_login"  # Utilise la vue de connexion d'allauth
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_SIGNUP_REDIRECT_URL = "/?login_required=true"
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)  # Restauré
ACCOUNT_ADAPTER = "booking.users.adapters.AccountAdapter"
ACCOUNT_FORMS = {"signup": "booking.users.forms.CustomSignupForm"}
SOCIALACCOUNT_ADAPTER = "booking.users.adapters.SocialAccountAdapter"
SOCIALACCOUNT_FORMS = {"signup": "booking.users.forms.UserSocialSignupForm"}

# SOCIALACCOUNT_PROVIDERS
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "facebook": {
        "METHOD": "oauth2",
        "SCOPE": ["email", "public_profile"],
        "AUTH_PARAMS": {"auth_type": "reauthenticate"},
    },
}

# PASSWORDS
# ------------------------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

# STATIC
# ------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [str(APPS_DIR / "static")]
STATIC_ROOT = str(BASE_DIR / "staticfiles")
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# MEDIA
# ------------------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media")

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "booking.users.context_processors.allauth_settings",
            ],
        },
    },
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# ALLOWED_HOSTS
# ------------------------------------------------------------------------------
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# FIXTURES
# ------------------------------------------------------------------------------
FIXTURE_DIRS = [str(APPS_DIR / "fixtures")]

# SECURITY
# ------------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = 0

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="apikey")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="asieniantour@gmail.com")
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
ADMIN_URL = "admin/"
ADMINS = [("""ella""", "ahou.405@gmail.com")]
MANAGERS = ADMINS
DJANGO_ADMIN_FORCE_ALLAUTH = env.bool("DJANGO_ADMIN_FORCE_ALLAUTH", False)

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

# CKEditor 5 Configuration
# ------------------------------------------------------------------------------
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "link", "bulletedList", "numberedList", "blockQuote", "imageUpload",
        ],
        "height": 300,
        "width": "auto",
    },
}

# Paystack Configuration
# ------------------------------------------------------------------------------
PAYSTACK_PUBLIC_KEY = env("PAYSTACK_PUBLIC_KEY", default="pk_test_ebe6f55be8b232118dfe69070aae2b879f97aac9")
PAYSTACK_SECRET_KEY = env("PAYSTACK_SECRET_KEY", default="sk_test_a65f398fe7d3193d595a951efc176b5041031fc3")
