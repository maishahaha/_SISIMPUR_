from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny

from apps.dashboard import views as dashboard_views

from . import views as brain_views

# ---------------------------------------------------------------------------
# Reusable response schemas
# ---------------------------------------------------------------------------
_err = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "error": openapi.Schema(type=openapi.TYPE_STRING),
    },
)
_job_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
        "document_name": openapi.Schema(type=openapi.TYPE_STRING),
        "status": openapi.Schema(type=openapi.TYPE_STRING),
        "language": openapi.Schema(type=openapi.TYPE_STRING),
        "question_type": openapi.Schema(type=openapi.TYPE_STRING),
        "created_at": openapi.Schema(type=openapi.TYPE_STRING),
        "qa_count": openapi.Schema(type=openapi.TYPE_INTEGER),
    },
)


# ---------------------------------------------------------------------------
# Document Processing
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="post",
    tags=["Brain - Document Processing"],
    operation_summary="Process document",
    operation_description="Upload a PDF, image, or text file to generate Q&A pairs.",
    manual_parameters=[
        openapi.Parameter("document", openapi.IN_FORM, description="Document file (PDF, JPG, PNG, TXT)", type=openapi.TYPE_FILE, required=True),
        openapi.Parameter("num_questions", openapi.IN_FORM, description="Number of questions to generate", type=openapi.TYPE_INTEGER, required=False),
        openapi.Parameter("language", openapi.IN_FORM, description="Language: auto | en | bn | ...", type=openapi.TYPE_STRING, required=False, default="auto"),
        openapi.Parameter("question_type", openapi.IN_FORM, description="MULTIPLECHOICE | SHORT", type=openapi.TYPE_STRING, required=False, default="MULTIPLECHOICE"),
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "job_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "qa_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                "message": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        400: _err,
    },
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def process_document(request):
    return brain_views.process_document(request._request)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="post",
    tags=["Brain - Evaluation"],
    operation_summary="Evaluate short answer",
    operation_description="Evaluate a single short-answer question for an active exam session.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["session_id", "q_id", "user_answer"],
        properties={
            "session_id": openapi.Schema(type=openapi.TYPE_STRING, description="UUID of the active exam session"),
            "q_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the QuestionAnswer object"),
            "user_answer": openapi.Schema(type=openapi.TYPE_STRING, description="The student's answer text"),
        },
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "evaluation": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "q_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "score": openapi.Schema(type=openapi.TYPE_NUMBER),
                        "max_score": openapi.Schema(type=openapi.TYPE_NUMBER),
                        "percentage": openapi.Schema(type=openapi.TYPE_NUMBER),
                        "feedback": openapi.Schema(type=openapi.TYPE_STRING),
                        "ideal_answer": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            },
        ),
        400: _err,
    },
)
@api_view(["POST"])
@parser_classes([JSONParser])
def evaluate_short_answer(request):
    return dashboard_views.evaluate_short_answer(request._request)


@swagger_auto_schema(
    method="post",
    tags=["Brain - Evaluation"],
    operation_summary="Store evaluation result",
    operation_description=(
        "Webhook endpoint — receives evaluation results from an external system (e.g. n8n) "
        "and stores them. Accepts either a direct object or an array wrapper from n8n."
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["exam_id", "data"],
        properties={
            "exam_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the ExamSession"),
            "data": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "q_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "user_answer": openapi.Schema(type=openapi.TYPE_STRING),
                    "score": openapi.Schema(type=openapi.TYPE_NUMBER),
                    "max_score": openapi.Schema(type=openapi.TYPE_NUMBER),
                    "feedback": openapi.Schema(type=openapi.TYPE_STRING),
                    "ideal_answer": openapi.Schema(type=openapi.TYPE_STRING),
                    "detailed_scores": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "accuracy": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "completeness": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "clarity": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "structure": openapi.Schema(type=openapi.TYPE_NUMBER),
                        },
                    ),
                },
            ),
        },
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={"success": openapi.Schema(type=openapi.TYPE_BOOLEAN), "message": openapi.Schema(type=openapi.TYPE_STRING)},
        ),
        400: _err,
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def store_evaluation_result(request):
    return dashboard_views.store_evaluation_result(request._request)


# ---------------------------------------------------------------------------
# Job management
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="get",
    tags=["Brain - Jobs"],
    operation_summary="List my jobs",
    operation_description="Return all processing jobs for the current user ordered by newest first.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "jobs": openapi.Schema(type=openapi.TYPE_ARRAY, items=_job_schema),
            },
        ),
    },
)
@api_view(["GET"])
def list_jobs(request):
    return brain_views.list_jobs(request._request)


@swagger_auto_schema(
    method="get",
    tags=["Brain - Jobs"],
    operation_summary="Get job status",
    operation_description="Return the current status and metadata of a processing job.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "job_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "status": openapi.Schema(type=openapi.TYPE_STRING, description="pending | processing | completed | failed"),
                "document_name": openapi.Schema(type=openapi.TYPE_STRING),
                "qa_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                "error_message": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        404: _err,
    },
)
@api_view(["GET"])
def get_job_status(request, job_id):
    return brain_views.get_job_status(request._request, job_id)


@swagger_auto_schema(
    method="get",
    tags=["Brain - Jobs"],
    operation_summary="Get job results",
    operation_description="Return all Q&A pairs for a completed job.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "job_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "qa_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                "questions": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            },
        ),
        400: _err,
        404: _err,
    },
)
@api_view(["GET"])
def get_job_results(request, job_id):
    return brain_views.get_job_results(request._request, job_id)


@swagger_auto_schema(
    method="get",
    tags=["Brain - Jobs"],
    operation_summary="Download job results",
    operation_description="Download Q&A results as a JSON file attachment.",
    responses={
        200: "JSON file download",
        400: _err,
        404: _err,
    },
)
@api_view(["GET"])
def download_results(request, job_id):
    return brain_views.download_results(request._request, job_id)


@swagger_auto_schema(
    method="delete",
    tags=["Brain - Jobs"],
    operation_summary="Delete job",
    operation_description="Permanently delete a processing job and all associated files and Q&A pairs.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={"success": openapi.Schema(type=openapi.TYPE_BOOLEAN), "message": openapi.Schema(type=openapi.TYPE_STRING)},
        ),
        404: _err,
    },
)
@api_view(["DELETE"])
def delete_job(request, job_id):
    return brain_views.delete_job(request._request, job_id)


# ---------------------------------------------------------------------------
# Admin / Development (served under /api/admin/brain/ only)
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="get",
    tags=["Admin - Development"],
    operation_summary="[Admin] Test document processing",
    operation_description="Staff-only: process a server-side file path and return generated Q&A as JSON.",
    manual_parameters=[
        openapi.Parameter("file", openapi.IN_QUERY, description="Absolute server path to the file", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter("questions", openapi.IN_QUERY, description="Number of questions (default 5)", type=openapi.TYPE_INTEGER, required=False),
        openapi.Parameter("language", openapi.IN_QUERY, description="Language override (default auto)", type=openapi.TYPE_STRING, required=False),
        openapi.Parameter("type", openapi.IN_QUERY, description="MULTIPLECHOICE | SHORT (default MULTIPLECHOICE)", type=openapi.TYPE_STRING, required=False),
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "job_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "questions_generated": openapi.Schema(type=openapi.TYPE_INTEGER),
                "results": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
        ),
        400: _err,
        403: _err,
    },
)
@api_view(["GET"])
def dev_test_processing(request):
    return brain_views.dev_test_processing(request._request)


@swagger_auto_schema(
    method="get",
    tags=["Admin - Development"],
    operation_summary="[Admin] List all jobs",
    operation_description="Staff-only: return the 20 most recent processing jobs across all users.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "total": openapi.Schema(type=openapi.TYPE_INTEGER),
                "jobs": openapi.Schema(type=openapi.TYPE_ARRAY, items=_job_schema),
            },
        ),
        403: _err,
    },
)
@api_view(["GET"])
def dev_list_jobs(request):
    return brain_views.dev_list_jobs(request._request)
