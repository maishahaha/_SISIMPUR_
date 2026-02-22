from django.urls import path
from . import api_views

app_name = "brain_admin"

urlpatterns = [
    path("dev/test/", api_views.dev_test_processing, name="admin_dev_test"),
    path("dev/jobs/", api_views.dev_list_jobs, name="admin_dev_jobs"),
]
