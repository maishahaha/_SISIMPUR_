from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser

from . import views as dashboard_views


# ---------------------------------------------------------------------------
# Quiz / Job results
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="get",
    tags=["Dashboard - Quizzes"],
    operation_summary="Get quiz results",
    operation_description="Retrieve generated Q&A pairs, form settings, and detected values for a completed job.",
    manual_parameters=[
        openapi.Parameter("format", openapi.IN_QUERY, description="Set to 'json' to force JSON response", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "job_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "questions_generated": openapi.Schema(type=openapi.TYPE_INTEGER),
                "qa_pairs": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                "form_settings": openapi.Schema(type=openapi.TYPE_OBJECT),
                "detected_values": openapi.Schema(type=openapi.TYPE_OBJECT),
                "generated_values": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
        ),
    },
)
@api_view(["GET"])
def quiz_results(request, job_id):
    # Force JSON response through the existing view
    req = request._request
    req.GET = req.GET.copy()
    req.GET["format"] = "json"
    return dashboard_views.quiz_results(req, job_id)


@swagger_auto_schema(
    method="get",
    tags=["Dashboard - Quizzes"],
    operation_summary="List my quizzes",
    operation_description="Return a JSON list of the current user's processing jobs.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "jobs": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            },
        ),
    },
)
@api_view(["GET"])
def my_quizzes(request):
    """Return the user's processing jobs as JSON."""
    from apps.brain.models import ProcessingJob
    from .models import ExamSession

    jobs = ProcessingJob.objects.filter(user=request.user).order_by("-created_at")
    data = []
    for job in jobs:
        latest_exam = (
            ExamSession.objects.filter(user=request.user, processing_job=job)
            .order_by("-started_at")
            .first()
        )
        data.append(
            {
                "id": job.id,
                "original_filename": job.original_filename,
                "status": job.status,
                "language": job.language,
                "question_type": job.question_type,
                "num_questions": job.num_questions,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "latest_exam_session_id": latest_exam.session_id if latest_exam else None,
            }
        )
    from django.http import JsonResponse

    return JsonResponse({"success": True, "jobs": data})


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="get",
    tags=["Dashboard - Leaderboard"],
    operation_summary="Leaderboard",
    operation_description="Return top-50 leaderboard data including rank, score, badges, and current user position.",
    manual_parameters=[
        openapi.Parameter(
            "filter",
            openapi.IN_QUERY,
            description="Time filter: all | week | month | year",
            type=openapi.TYPE_STRING,
            default="all",
        ),
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "leaderboard": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                "current_user_rank": openapi.Schema(type=openapi.TYPE_INTEGER, x_nullable=True),
            },
        ),
    },
)
@api_view(["GET"])
def leaderboard(request):
    """JSON leaderboard endpoint (mirrors template logic)."""
    from django.contrib.auth.models import User
    from django.db.models import Avg, Count, Q, Sum
    from datetime import timedelta
    from django.utils import timezone as tz
    from django.http import JsonResponse
    from .models import ExamSession

    filter_type = request.query_params.get("filter", "all")
    now = tz.now()
    start_date = {
        "week": now - timedelta(days=7),
        "month": now - timedelta(days=30),
        "year": now - timedelta(days=365),
    }.get(filter_type)

    sessions = ExamSession.objects.filter(status="completed")
    if start_date:
        sessions = sessions.filter(completed_at__gte=start_date)

    user_stats = (
        User.objects.annotate(
            total_exams=Count("exam_sessions", filter=Q(exam_sessions__in=sessions)),
            total_score=Sum("exam_sessions__total_score", filter=Q(exam_sessions__in=sessions)),
            avg_percentage=Avg("exam_sessions__percentage_score", filter=Q(exam_sessions__in=sessions)),
            total_credit_points=Sum("exam_sessions__credit_points", filter=Q(exam_sessions__in=sessions)),
        )
        .filter(total_exams__gt=0)
        .order_by("-total_score", "-avg_percentage", "-total_exams")[:50]
    )

    items = []
    current_user_rank = None
    for rank, u in enumerate(user_stats, 1):
        is_current = u.pk == request.user.pk
        if is_current:
            current_user_rank = rank
        items.append(
            {
                "rank": rank,
                "username": u.username,
                "full_name": u.get_full_name(),
                "total_score": u.total_score or 0,
                "total_exams": u.total_exams or 0,
                "avg_percentage": round(u.avg_percentage or 0, 1),
                "total_credit_points": u.total_credit_points or 0,
                "is_current_user": is_current,
            }
        )

    return JsonResponse({"success": True, "leaderboard": items, "current_user_rank": current_user_rank, "filter": filter_type})


# ---------------------------------------------------------------------------
# Exam lifecycle
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="post",
    tags=["Dashboard - Exams"],
    operation_summary="Start exam",
    operation_description="Create a new exam session for a completed processing job and return the session id.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "session_id": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    },
)
@api_view(["POST"])
def start_exam(request, job_id):
    """Start an exam and return the new session_id as JSON instead of redirecting."""
    import uuid
    import random
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from apps.brain.models import ProcessingJob
    from .models import ExamSession, ExamConfiguration

    try:
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)
        if job.status != "completed":
            return JsonResponse({"success": False, "error": "Job not completed"}, status=400)

        qa_pairs = job.get_qa_pairs()
        if not qa_pairs.exists():
            return JsonResponse({"success": False, "error": "No questions found"}, status=400)

        config = ExamConfiguration.get_current_config()
        session_id = str(uuid.uuid4())
        questions_list = list(qa_pairs.values_list("id", flat=True))
        random.shuffle(questions_list)

        user_attempts = ExamSession.objects.filter(user=request.user, processing_job=job).count()

        ExamSession.objects.create(
            user=request.user,
            processing_job=job,
            session_id=session_id,
            total_questions=len(questions_list),
            time_limit_minutes=len(questions_list) * config.default_time_per_question_minutes,
            allow_navigation=config.allow_question_navigation,
            max_attempts=999,
            attempt_number=user_attempts + 1,
            questions_order=questions_list,
        )
        return JsonResponse({"success": True, "session_id": session_id})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@swagger_auto_schema(
    method="get",
    tags=["Dashboard - Exams"],
    operation_summary="Get exam session state",
    operation_description="Retrieve the current question and progress for an active exam session.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "current_index": openapi.Schema(type=openapi.TYPE_INTEGER),
                "total_questions": openapi.Schema(type=openapi.TYPE_INTEGER),
                "question": openapi.Schema(type=openapi.TYPE_OBJECT),
                "remaining_time": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
    },
)
@api_view(["GET"])
def exam_session(request, session_id):
    """Return current exam state as JSON."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import ExamSession, ExamAnswer
    from apps.brain.models import QuestionAnswer

    try:
        es = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        if es.status != "active":
            return JsonResponse({"success": False, "error": "Exam not active", "status": es.status})

        idx = es.current_question_index
        if idx >= len(es.questions_order):
            return JsonResponse({"success": False, "error": "All questions answered"})

        q = get_object_or_404(QuestionAnswer, id=es.questions_order[idx])
        existing = ExamAnswer.objects.filter(exam_session=es, question=q).first()

        q_data = {
            "id": q.id,
            "question": q.question,
            "question_type": q.question_type,
            "options": q.options if q.question_type == "MULTIPLECHOICE" else None,
        }

        return JsonResponse(
            {
                "success": True,
                "session_status": es.status,
                "current_index": idx,
                "total_questions": len(es.questions_order),
                "question": q_data,
                "existing_answer": existing.user_answer if existing else None,
                "remaining_time": es.get_remaining_time_seconds(),
                "can_go_back": idx > 0 and es.allow_navigation,
                "can_go_next": idx < len(es.questions_order) - 1,
                "is_last_question": idx == len(es.questions_order) - 1,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@swagger_auto_schema(
    method="post",
    tags=["Dashboard - Exams"],
    operation_summary="Submit exam answer",
    operation_description="Submit an answer for the current question and optionally navigate or submit the exam.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "answer": openapi.Schema(type=openapi.TYPE_STRING),
            "action": openapi.Schema(type=openapi.TYPE_STRING, description="next | previous | submit"),
        },
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "current_index": openapi.Schema(type=openapi.TYPE_INTEGER),
                "completed": openapi.Schema(type=openapi.TYPE_BOOLEAN),
            },
        ),
    },
)
@api_view(["POST"])
@parser_classes([JSONParser])
def answer_question(request, session_id):
    """Accept answer JSON and advance question index; return new state."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from django.utils import timezone as tz
    from .models import ExamSession, ExamAnswer
    from apps.brain.models import QuestionAnswer
    from apps.utils import send_exam_completion_webhook

    try:
        es = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        if es.status != "active":
            return JsonResponse({"success": False, "error": "Exam not active"}, status=400)

        data = request.data
        user_answer = (data.get("answer") or "").strip()
        action = data.get("action", "next")

        idx = es.current_question_index
        q = get_object_or_404(QuestionAnswer, id=es.questions_order[idx])

        # Save answer
        if user_answer:
            from apps.dashboard.views import evaluate_answer as _eval
            is_correct = False
            if q.question_type != "SHORT":
                is_correct, _ = _eval(user_answer, q)

            ExamAnswer.objects.update_or_create(
                exam_session=es,
                question=q,
                defaults={
                    "question_index": idx,
                    "user_answer": user_answer,
                    "is_correct": is_correct,
                },
            )

        # Navigate
        completed = False
        if action == "next" and idx < len(es.questions_order) - 1:
            es.current_question_index += 1
        elif action == "previous" and idx > 0 and es.allow_navigation:
            es.current_question_index -= 1
        elif action == "submit":
            es.status = "completed"
            es.completed_at = tz.now()
            es.calculate_score()
            completed = True
            send_exam_completion_webhook(request.user, es)

        es.save()
        return JsonResponse({"success": True, "current_index": es.current_question_index, "completed": completed})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@swagger_auto_schema(
    method="post",
    tags=["Dashboard - Exams"],
    operation_summary="Submit exam",
    operation_description="Forcefully complete and score the exam session.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "session_id": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    },
)
@api_view(["POST"])
def submit_exam(request, session_id):
    """Complete the exam."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from django.utils import timezone as tz
    from .models import ExamSession
    from apps.utils import send_exam_completion_webhook

    try:
        es = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        if es.status == "active":
            es.status = "completed"
            es.completed_at = tz.now()
            es.calculate_score()
            es.save()
            send_exam_completion_webhook(request.user, es)
        return JsonResponse({"success": True, "session_id": session_id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@swagger_auto_schema(
    method="get",
    tags=["Dashboard - Exams"],
    operation_summary="Get exam result",
    operation_description="Return detailed exam results including answers, scores, and short-answer evaluations.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "total_questions": openapi.Schema(type=openapi.TYPE_INTEGER),
                "correct_answers": openapi.Schema(type=openapi.TYPE_INTEGER),
                "answers": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            },
        ),
    },
)
@api_view(["GET"])
def exam_result(request, session_id):
    """Return exam results as JSON."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import ExamSession, ExamAnswer, ShortAnswerEvaluation

    try:
        es = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        if es.status == "active":
            return JsonResponse({"success": False, "error": "Exam still active"}, status=400)

        answers = ExamAnswer.objects.filter(exam_session=es).order_by("question_index")
        short_evals = ShortAnswerEvaluation.objects.filter(exam_session=es).order_by("question_index")

        answers_data = [
            {
                "question_index": a.question_index,
                "question": a.question.question,
                "question_type": a.question.question_type,
                "user_answer": a.user_answer,
                "correct_answer": a.question.answer,
                "is_correct": a.is_correct,
            }
            for a in answers
        ]

        evals_data = [
            {
                "question_index": e.question_index,
                "score": e.score,
                "max_score": e.max_score,
                "feedback": e.feedback,
                "accuracy_score": e.accuracy_score,
                "completeness_score": e.completeness_score,
                "clarity_score": e.clarity_score,
            }
            for e in short_evals
        ]

        correct = answers.filter(is_correct=True).count()
        return JsonResponse(
            {
                "success": True,
                "session_id": session_id,
                "status": es.status,
                "total_questions": es.total_questions,
                "answered_questions": answers.count(),
                "correct_answers": correct,
                "incorrect_answers": answers.count() - correct,
                "percentage_score": es.percentage_score,
                "answers": answers_data,
                "short_answer_evaluations": evals_data,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------

@swagger_auto_schema(
    method="post",
    tags=["Dashboard - Flashcards"],
    operation_summary="Start flashcard session",
    operation_description="Create a new flashcard session for a completed processing job.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "session_id": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    },
)
@api_view(["POST"])
def start_flashcard(request, job_id):
    """Start flashcard session and return session_id as JSON."""
    import uuid
    import random
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from apps.brain.models import ProcessingJob
    from .models import FlashcardSession, ExamConfiguration

    try:
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)
        if job.status != "completed":
            return JsonResponse({"success": False, "error": "Job not completed"}, status=400)

        qa_pairs = job.get_qa_pairs()
        if not qa_pairs.exists():
            return JsonResponse({"success": False, "error": "No questions found"}, status=400)

        config = ExamConfiguration.get_current_config()
        session_id = str(uuid.uuid4())
        cards = list(qa_pairs.values_list("id", flat=True))
        random.shuffle(cards)

        FlashcardSession.objects.create(
            user=request.user,
            processing_job=job,
            session_id=session_id,
            total_cards=len(cards),
            time_per_card_seconds=config.default_flashcard_time_seconds,
            auto_advance=config.auto_advance_flashcards,
            cards_order=cards,
        )
        return JsonResponse({"success": True, "session_id": session_id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@swagger_auto_schema(
    method="get",
    tags=["Dashboard - Flashcards"],
    operation_summary="Get flashcard state",
    operation_description="Get the current flashcard and progress for an active session.",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "current_index": openapi.Schema(type=openapi.TYPE_INTEGER),
                "total_cards": openapi.Schema(type=openapi.TYPE_INTEGER),
                "card": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
        ),
    },
)
@api_view(["GET"])
def flashcard_session(request, session_id):
    """Return current flashcard as JSON."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import FlashcardSession
    from apps.brain.models import QuestionAnswer

    try:
        fs = get_object_or_404(FlashcardSession, session_id=session_id, user=request.user)
        if fs.status != "active":
            return JsonResponse({"success": False, "error": "Session not active", "status": fs.status})

        idx = fs.current_card_index
        if idx >= len(fs.cards_order):
            return JsonResponse({"success": False, "error": "All cards viewed"})

        card = get_object_or_404(QuestionAnswer, id=fs.cards_order[idx])
        return JsonResponse(
            {
                "success": True,
                "current_index": idx,
                "total_cards": len(fs.cards_order),
                "progress_percentage": round(idx / len(fs.cards_order) * 100, 1),
                "is_last_card": idx == len(fs.cards_order) - 1,
                "card": {
                    "id": card.id,
                    "question": card.question,
                    "answer": card.answer,
                    "question_type": card.question_type,
                },
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@swagger_auto_schema(
    method="post",
    tags=["Dashboard - Flashcards"],
    operation_summary="Advance flashcard",
    operation_description="Record progress on the current card and move to the next one.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "action": openapi.Schema(type=openapi.TYPE_STRING, description="next | skip"),
        },
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "completed": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "current_index": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
    },
)
@api_view(["POST"])
@parser_classes([JSONParser])
def advance_flashcard(request, session_id):
    """Record progress and advance."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from django.utils import timezone as tz
    from .models import FlashcardSession, FlashcardProgress
    from apps.brain.models import QuestionAnswer

    try:
        fs = get_object_or_404(FlashcardSession, session_id=session_id, user=request.user)
        if fs.status != "active":
            return JsonResponse({"success": False, "error": "Session not active"}, status=400)

        action = request.data.get("action", "next")
        idx = fs.current_card_index
        card = get_object_or_404(QuestionAnswer, id=fs.cards_order[idx])

        FlashcardProgress.objects.update_or_create(
            flashcard_session=fs,
            question=card,
            defaults={"card_index": idx, "was_skipped": action == "skip", "time_spent_seconds": 60},
        )

        fs.current_card_index += 1
        fs.cards_studied += 1
        completed = fs.current_card_index >= len(fs.cards_order)
        if completed:
            fs.status = "completed"
            fs.completed_at = tz.now()
        fs.save()

        return JsonResponse({"success": True, "completed": completed, "current_index": fs.current_card_index})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
