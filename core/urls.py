from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.frontend.views import health_check
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ---------------------------------------------------------------------------
# Public API schema (all non-admin endpoints)
# ---------------------------------------------------------------------------
_public_patterns = [
    path("api/auth/", include("apps.authentication.api_urls")),
    path("api/dashboard/", include("apps.dashboard.api_urls")),
    path("api/brain/", include("apps.brain.urls")),
]

schema_view = get_schema_view(
    openapi.Info(
        title="Sisimpur API",
        default_version="v1",
        description=(
            "API documentation for **Sisimpur** backend services.\n\n"
            "## Categories\n"
            "| Group | Description |\n"
            "|-------|-------------|\n"
            "| **Auth** | Registration, login, OTP verification & Google OAuth |\n"
            "| **Brain** | Document processing, Q&A generation, evaluation |\n"
            "| **Dashboard** | Quizzes, exams, flashcards & leaderboard |\n"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=_public_patterns,
)

# ---------------------------------------------------------------------------
# Admin-only schema (dev/diagnostic endpoints only)
# ---------------------------------------------------------------------------
_admin_patterns = [
    path("api/admin/brain/", include("apps.brain.admin_urls")),
]

admin_schema_view = get_schema_view(
    openapi.Info(
        title="Sisimpur Admin API",
        default_version="v1",
        description=(
            "**Admin / diagnostic endpoints** for Sisimpur backend.\n\n"
            "These endpoints are intended for staff inspection and development only."
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=_admin_patterns,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health_check, name="health_check"),  # Health check endpoint
    path("api/docs/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc-ui"),
    path("api/swagger.json", schema_view.without_ui(cache_timeout=0), name="swagger-json"),
    # Admin docs — scoped schema showing only dev/diagnostic endpoints
    path("api/admin/docs/", admin_schema_view.with_ui("swagger", cache_timeout=0), name="admin-swagger-ui"),
    path("api/admin/redoc/", admin_schema_view.with_ui("redoc", cache_timeout=0), name="admin-redoc-ui"),
    path("", include("apps.frontend.urls")),
    path("auth/", include("apps.authentication.urls")),
    path("api/auth/", include("apps.authentication.api_urls")),
    path("api/dashboard/", include("apps.dashboard.api_urls")),
    path("api/brain/", include("apps.brain.urls")),
    path("api/admin/brain/", include("apps.brain.admin_urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add django-browser-reload URLs only in DEBUG mode
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
