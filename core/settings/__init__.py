"""
Auto-selects settings module based on DJANGO_ENV environment variable.

  DJANGO_ENV=production  → uses core.settings.production
  DJANGO_ENV=development  → uses core.settings.development (default)

Set DJANGO_ENV in your server environment or .env file.
"""
import os

_env = os.getenv("DJANGO_ENV", "development")

if _env == "production":
    from .production import *
else:
    from .development import *
