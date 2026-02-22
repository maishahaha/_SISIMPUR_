"""
Production settings.
Active when DJANGO_ENV=production.

Required environment variables:
  DJANGO_SECRET_KEY      — strong random key
  DATABASE_URL           — Neon PostgreSQL connection string
  DJANGO_ALLOWED_HOSTS   — comma-separated hostnames  e.g. "sisimpur.onrender.com"
  WEBSITE_URL            — public base URL  e.g. "https://sisimpur.onrender.com"
  CORS_ALLOWED_ORIGINS   — comma-separated allowed origins for the React frontend
"""
import os
from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = False

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "sisimpur.onrender.com").split(",")
    if h.strip()
]

WEBSITE_URL = os.getenv("WEBSITE_URL", "https://sisimpur.onrender.com")
GOOGLE_OAUTH2_REDIRECT_URI = f"{WEBSITE_URL}/auth/google-callback/"

# ---------------------------------------------------------------------------
# CORS / CSRF  (override from base with production origins)
# ---------------------------------------------------------------------------
_extra_origins = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
CORS_ALLOWED_ORIGINS = (  # noqa: F405
    CORS_ALLOWED_ORIGINS + _extra_origins  # noqa: F405
)
CSRF_TRUSTED_ORIGINS = (  # noqa: F405
    CSRF_TRUSTED_ORIGINS + _extra_origins  # noqa: F405
)

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
