from django.conf import settings
from django.http import JsonResponse


class ComingSoonMiddleware:
    """
    When COMING_SOON=True in settings, every non-admin / non-API request
    returns a 503 JSON response so the React frontend can show a coming-soon
    page.  Toggle COMING_SOON=False to disable.
    """

    _PASSTHROUGH_PREFIXES = ("/admin/", "/api/", "/static/", "/media/", "/__reload__/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.COMING_SOON and not any(
            request.path.startswith(p) for p in self._PASSTHROUGH_PREFIXES
        ):
            return JsonResponse(
                {
                    "detail": "Site is coming soon.",
                    "target_date": settings.COMING_SOON_TARGET_DATE,
                },
                status=503,
            )
        return self.get_response(request)
