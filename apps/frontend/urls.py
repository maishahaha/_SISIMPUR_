from django.urls import path
from . import views

urlpatterns = [
    path('', views.backend_root, name='root'),
    path('submit-and-subscribe/', views.submit_and_subscribe, name='submit_and_subscribe'),
]