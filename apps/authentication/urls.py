from django.urls import path
from . import views

app_name = "auth"

# Template-based signupin/verify-otp routes removed — React frontend handles UI.
# Google OAuth and session logout remain server-side.
urlpatterns = [
    path("send-otp/", views.send_otp_ajax, name="send_otp"),
    path("verify-otp-ajax/", views.verify_otp_ajax, name="verify_otp_ajax"),
    path("logout/", views.logout_view, name="logout"),
    path("google-login/", views.google_login, name="google_login"),
    path("google-callback/", views.google_callback, name="google_callback"),
]
