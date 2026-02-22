"""
Development settings.
Active when DJANGO_ENV is unset or set to "development".
Never use in production.
"""
import os
from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = True
ALLOWED_HOSTS = ["*"]

WEBSITE_URL = os.getenv("WEBSITE_URL", "http://localhost:8000")
GOOGLE_OAUTH2_REDIRECT_URI = f"{WEBSITE_URL}/auth/google-callback/"

# Allow HTTP for OAuth locally
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# ---------------------------------------------------------------------------
# django-browser-reload (hot-reload for any remaining Django-rendered pages)
# ---------------------------------------------------------------------------
INSTALLED_APPS = INSTALLED_APPS + ["django_browser_reload"]  # noqa: F405

_common_idx = MIDDLEWARE.index("django.middleware.common.CommonMiddleware")  # noqa: F405
MIDDLEWARE = (  # noqa: F405
    MIDDLEWARE[:_common_idx + 1]
    + ["django_browser_reload.middleware.BrowserReloadMiddleware"]
    + MIDDLEWARE[_common_idx + 1:]
)

# ---------------------------------------------------------------------------
# Email — console backend during development (no real emails sent)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
