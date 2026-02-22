from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny

from apps.dashboard import views as dashboard_views

from . import views as brain_views


@swagger_auto_schema(
    method="post",
    tags=["Brain - Document Processing"],
    operation_summary="Process document",
    operation_description="Upload a document and generate questions.",
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def process_document(request):
    return brain_views.process_document(request._request)


@swagger_auto_schema(
    method="post",
    tags=["Brain - Evaluation"],
    operation_summary="Evaluate short answer",
    operation_description="Evaluate a short answer for the current exam session.",
)
@api_view(["POST"])
@parser_classes([JSONParser])
def evaluate_short_answer(request):
    return dashboard_views.evaluate_short_answer(request._request)


@swagger_auto_schema(
    method="post",
    tags=["Brain - Evaluation"],
    operation_summary="Store evaluation result",
    operation_description="Store short-answer evaluation results (webhook-friendly endpoint).",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def store_evaluation_result(request):
    return dashboard_views.store_evaluation_result(request._request)


@swagger_auto_schema(method="get", tags=["Brain - Jobs"], operation_summary="List jobs")
@api_view(["GET"])
def list_jobs(request):
    return brain_views.list_jobs(request._request)


@swagger_auto_schema(method="get", tags=["Brain - Jobs"], operation_summary="Get job status")
@api_view(["GET"])
def get_job_status(request, job_id):
    return brain_views.get_job_status(request._request, job_id)


@swagger_auto_schema(method="get", tags=["Brain - Jobs"], operation_summary="Get job results")
@api_view(["GET"])
def get_job_results(request, job_id):
    return brain_views.get_job_results(request._request, job_id)


@swagger_auto_schema(method="get", tags=["Brain - Jobs"], operation_summary="Download job results")
@api_view(["GET"])
def download_results(request, job_id):
    return brain_views.download_results(request._request, job_id)


@swagger_auto_schema(method="delete", tags=["Brain - Jobs"], operation_summary="Delete job")
@api_view(["DELETE"])
def delete_job(request, job_id):
    return brain_views.delete_job(request._request, job_id)


@swagger_auto_schema(method="get", tags=["Brain - Development"], operation_summary="Development test processing")
@api_view(["GET"])
def dev_test_processing(request):
    return brain_views.dev_test_processing(request._request)


@swagger_auto_schema(method="get", tags=["Brain - Development"], operation_summary="Development list jobs")
@api_view(["GET"])
def dev_list_jobs(request):
    return brain_views.dev_list_jobs(request._request)
