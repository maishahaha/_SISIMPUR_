# Template-serving dashboard routes removed — React frontend handles all UI.
# All data is served via REST API at api/dashboard/ (see api_urls.py).

from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = []