from django.urls import path
from . import api_views

app_name = "brain"

urlpatterns = [
    # Document processing endpoints (OCR + Question Generation Pipeline)
    path('process/document/', api_views.process_document, name='process_document'),

    # Short answer evaluation endpoints
    path('evaluate-short-answer/', api_views.evaluate_short_answer, name='evaluate_short_answer'),
    path('store-evaluation-result/', api_views.store_evaluation_result, name='store_evaluation_result'),

    # Job management endpoints
    path('jobs/', api_views.list_jobs, name='list_jobs'),
    path('jobs/<int:job_id>/status/', api_views.get_job_status, name='job_status'),
    path('jobs/<int:job_id>/results/', api_views.get_job_results, name='job_results'),
    path('jobs/<int:job_id>/download/', api_views.download_results, name='download_results'),
    path('jobs/<int:job_id>/delete/', api_views.delete_job, name='delete_job'),

]

