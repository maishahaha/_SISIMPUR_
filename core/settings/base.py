"""
Base settings shared across all environments.
Do NOT reference this file directly — import via core.settings (auto-routes via __init__.py).
"""

import sys
from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# base.py lives at core/settings/base.py, so project root is three levels up
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "apps"))

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_yasg",
    "corsheaders",
    # Internal apps
    "apps.authentication",
    "apps.frontend",
    "apps.dashboard",
    "apps.brain",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "core.middleware.ComingSoonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],   # No Django templates — React handles all UI
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.static",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# ---------------------------------------------------------------------------
# Database — Neon PostgreSQL
# ---------------------------------------------------------------------------
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Sites framework
# ---------------------------------------------------------------------------
SITE_ID = 1

# ---------------------------------------------------------------------------
# Coming-soon mode  (flip to True + set date to lock the site)
# ---------------------------------------------------------------------------
COMING_SOON = False
COMING_SOON_TARGET_DATE = "2025-07-10T00:00:00Z"

# ---------------------------------------------------------------------------
# Brain / AI engine
# ---------------------------------------------------------------------------
BRAIN_CONFIG = {
    "GEMINI_API_KEY": os.getenv("GOOGLE_API_KEY"),
    "MAX_RETRIES": 5,
    "INITIAL_RETRY_DELAY": 2,
    "MAX_RETRY_DELAY": 60,
    "RATE_LIMIT_BATCH_SIZE": 3,
    "RATE_LIMIT_COOLDOWN": 10,
    "DEFAULT_GEMINI_MODEL": "models/gemini-1.5-flash",
    "QA_GEMINI_MODEL": "models/gemini-1.5-flash",
    "FALLBACK_GEMINI_MODEL": "models/gemini-1.5-flash",
    "MIN_TEXT_LENGTH": 100,
    "QUESTION_TYPE": "MULTIPLECHOICE",
    "ANSWER_OPTIONS": 4,
}

BRAIN_TEMP_DIR = MEDIA_ROOT / "brain" / "temp_extracts"
BRAIN_OUTPUT_DIR = MEDIA_ROOT / "brain" / "qa_outputs"
BRAIN_UPLOADS_DIR = MEDIA_ROOT / "brain" / "uploads"

BRAIN_TEMP_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ---------------------------------------------------------------------------
# Django REST Framework + Simple JWT
# ---------------------------------------------------------------------------

# Set API_REQUIRE_AUTH=true in environment to enforce JWT authentication on all API endpoints.
# Defaults to False so all API endpoints are publicly accessible during development.
API_REQUIRE_AUTH = os.getenv("API_REQUIRE_AUTH", "false").lower() == "true"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"
        if API_REQUIRE_AUTH
        else "rest_framework.permissions.AllowAny"
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------------------
# Email (SMTP via Gmail by default)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# ---------------------------------------------------------------------------
# OTP
# ---------------------------------------------------------------------------
OTP_CONFIG = {
    "OTP_LENGTH": 6,
    "OTP_EXPIRY_MINUTES": 5,
    "MAX_OTP_ATTEMPTS": 3,
    "RESEND_COOLDOWN_MINUTES": 2,
    "MAX_HOURLY_ATTEMPTS": 5,
    "BLOCK_DURATION_HOURS": 1,
    "CLEANUP_INTERVAL_HOURS": 24,
}

# ---------------------------------------------------------------------------
# Google OAuth2
# ---------------------------------------------------------------------------
GOOGLE_OAUTH2_CLIENT_ID = os.getenv("GOOGLE_OAUTH2_CLIENT_ID")
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH2_CLIENT_SECRET")

# ---------------------------------------------------------------------------
# CORS / CSRF / Sessions  (extended in dev/prod)
# ---------------------------------------------------------------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ---------------------------------------------------------------------------
# Swagger / drf-yasg
# ---------------------------------------------------------------------------
SWAGGER_SETTINGS = {
    "DEFAULT_INFO": "core.urls.schema_view",
    "USE_SESSION_AUTH": True,
    "TAGS_SORTER": "alpha",
    "OPERATIONS_SORTER": "alpha",
    "DOC_EXPANSION": "list",
    "DEEP_LINKING": True,
    "DISPLAY_OPERATION_ID": False,
}
