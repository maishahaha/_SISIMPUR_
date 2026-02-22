from django.shortcuts import render, redirect, get_object_or_404
# DEV ONLY: Bypass auth — revert before production
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
import uuid
import random
import json
from .models import ExamSession, ShortAnswerEvaluation, ExamAnswer
from .forms import ExamRequestForm
from apps.utils import send_document_processing_success_webhook, send_document_processing_failed_webhook, send_exam_completion_webhook
from apps.brain.provider import APIService

@login_required(login_url='auth:signupin')
def home(request):
    """
    Render the home page of the dashboard.
    """
    # Get recent processing jobs for the user
    try:
        from apps.brain.models import ProcessingJob
        recent_jobs = ProcessingJob.objects.filter(user=request.user).order_by('-created_at')[:5]
    except:
        recent_jobs = []

    context = {
        'recent_jobs': recent_jobs
    }
    return render(request, "dashboard.html", context)

def logout_redirect(request):
    """Redirect to auth logout"""
    return redirect('auth:logout')

@login_required(login_url='auth:signupin')
def profile(request):
    """
    Render the user profile page
    """
    return render(request, "profile.html")

@login_required(login_url='auth:signupin')
def settings(request):
    """
    Render the settings page
    """
    return render(request, "settings.html")

@login_required(login_url='auth:signupin')
def help(request):
    """
    Render the help and support page
    """
    return render(request, "help.html")

@login_required(login_url='auth:signupin')
def quiz_generator(request):
    """
    Render the quiz generator page
    """
    return render(request, "quiz_generator.html")

@login_required(login_url='auth:signupin')
def my_quizzes(request):
    """
    Render the my quizzes page with user's processing jobs
    """
    try:
        from apps.brain.models import ProcessingJob
        from .models import ExamSession, ShortAnswerEvaluation, ExamAnswer, ExamConfiguration

        jobs = ProcessingJob.objects.filter(user=request.user).order_by('-created_at')

        # Add latest exam session info for results (no attempt limits)
        for job in jobs:
            # Get the latest exam session for results only
            latest_exam = ExamSession.objects.filter(
                user=request.user,
                processing_job=job
            ).order_by('-started_at').first()

            job.latest_exam = latest_exam
    except:
        jobs = []

    context = {
        'jobs': jobs
    }
    return render(request, "my_quizzes.html", context)

@login_required(login_url='auth:signupin')
def quiz_results(request, job_id):
    """
    Render the quiz results page for a specific job
    """
    try:
        from apps.brain.models import ProcessingJob
        from django.shortcuts import get_object_or_404

        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)
        qa_pairs = job.get_qa_pairs() if job.status == 'completed' else []
    except:
        job = None
        qa_pairs = []

    # Convert each QA pair to a dictionary with full details
    serialized_qa_pairs = []
    for qa in qa_pairs:
        qa_dict = {
            'question': qa.question,
            'answer': qa.answer,
            'question_type': qa.question_type,
        }

        # Add multiple choice specific fields
        if qa.question_type == 'MULTIPLECHOICE' and qa.options:
            qa_dict['options'] = qa.options
            qa_dict['correct_option'] = qa.correct_option

        # Add metadata if available
        if qa.confidence_score is not None:
            qa_dict['confidence_score'] = qa.confidence_score

        serialized_qa_pairs.append(qa_dict)

    # Prepare form settings and detected values
    form_settings = {}
    detected_values = {}
    generated_values = {}

    if job:
        # Form settings (what user selected)
        form_settings = {
            'selected_language': job.language,
            'selected_question_type': job.question_type,
            'selected_num_questions': job.num_questions,
            'selected_document_type': job.document_type,
        }

        # Detected values (what system detected)
        metadata = job.processing_metadata or {}
        detected_values = {
            'detected_language': metadata.get('language', 'unknown'),
            'detected_document_type': metadata.get('doc_type', 'unknown'),
            'detected_is_question_paper': metadata.get('is_question_paper', False),
            'detected_pdf_type': metadata.get('pdf_type'),
            'file_size': metadata.get('file_size'),
            'file_extension': metadata.get('extension'),
        }

        # Add human-readable labels
        form_settings['selected_language_display'] = dict(job.LANGUAGE_CHOICES).get(job.language, job.language)
        form_settings['selected_question_type_display'] = dict(job.QUESTION_TYPE_CHOICES).get(job.question_type, job.question_type)

        detected_values['detected_language_display'] = {
            'bengali': 'Bengali', 'english': 'English', 'unknown': 'Unknown'
        }.get(detected_values['detected_language'], detected_values['detected_language'])

        # Generated values (actual results)
        generated_values = {
            'generated_num_questions': len(serialized_qa_pairs),
            'generated_question_types': list(set(qa.question_type for qa in qa_pairs)),
            'processing_status': job.status,
            'processing_time': (job.completed_at - job.created_at).total_seconds() if job.completed_at else None,
        }

    # Check if this is an AJAX request (for API usage)
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'message': 'Quiz results retrieved successfully',
            'questions_generated': len(serialized_qa_pairs),
            'qa_pairs': serialized_qa_pairs,
            'form_settings': form_settings,
            'detected_values': detected_values,
            'generated_values': generated_values,
        })

    # Render template for regular page access
    context = {
        'job': job,
        'qa_pairs': qa_pairs,
        'serialized_qa_pairs': serialized_qa_pairs,
        'form_settings': form_settings,
        'detected_values': detected_values,
        'generated_values': generated_values,
    }
    return render(request, "quiz_results.html", context)

# API endpoints for AJAX calls
@login_required(login_url='auth:signupin')
@csrf_exempt
@require_http_methods(["POST"])
def api_process_document(request):
    """
    API endpoint to process documents via AJAX (OCR + Question Generation Pipeline)
    Handles file upload and storage using Django's file system
    """
    try:
        # Validate request
        if 'document' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No document file provided'
            }, status=400)

        uploaded_file = request.FILES['document']

        # Validate file type
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = uploaded_file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Please upload PDF, JPG, or PNG files.'
            }, status=400)

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File size too large. Maximum size is 10MB.'
            }, status=400)

        # Get form data
        language = request.POST.get('language', 'auto')
        question_type = request.POST.get('question_type', 'MULTIPLECHOICE')
        num_questions = request.POST.get('num_questions')

        # Convert num_questions to int if provided
        if num_questions:
            try:
                num_questions = int(num_questions)
            except ValueError:
                num_questions = None

        # Import brain models and create job
        from apps.brain.models import ProcessingJob
        from django.core.files.storage import default_storage

        # Create processing job
        job = ProcessingJob.objects.create(
            user=request.user,
            document_name=uploaded_file.name,
            language=language,
            num_questions=num_questions,
            question_type=question_type,
            status='pending'
        )

        # Save uploaded file
        file_path = f'brain/uploads/{job.id}_{uploaded_file.name}'
        saved_path = default_storage.save(file_path, uploaded_file)

        # Update job with file path
        job.document_file = saved_path
        job.save()

        # Start processing in background thread
        from apps.brain.services import BackgroundProcessor
        BackgroundProcessor.process_job_in_background(job.id)

        # Return immediate response
        return JsonResponse({
            'success': True,
            'job_id': job.id,
            'message': 'Document processing started in background',
            'processing_method': 'API_ASYNC'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)

@login_required(login_url='auth:signupin')
def api_job_status(request, job_id):
    """
    API endpoint to get job status
    """
    try:
        from apps.brain.views import get_job_status
        return get_job_status(request, job_id)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Brain processing not available: {str(e)}'
        }, status=500)


# ============================================================================
# LEADERBOARD FUNCTIONALITY
# ============================================================================

@login_required(login_url='auth:signupin')
def leaderboard(request):
    """
    Display global leaderboard with user rankings based on exam performance
    """
    from django.db.models import Count, Avg, Sum, Q
    from django.contrib.auth.models import User
    from datetime import datetime, timedelta

    # Get filter parameter
    filter_type = request.GET.get('filter', 'all')

    # Calculate date range based on filter
    now = timezone.now()
    if filter_type == 'week':
        start_date = now - timedelta(days=7)
    elif filter_type == 'month':
        start_date = now - timedelta(days=30)
    elif filter_type == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = None

    # Base queryset for exam sessions
    exam_sessions = ExamSession.objects.filter(status='completed')
    if start_date:
        exam_sessions = exam_sessions.filter(completed_at__gte=start_date)

    # Calculate user statistics
    user_stats = User.objects.annotate(
        total_exams=Count('exam_sessions', filter=Q(exam_sessions__in=exam_sessions)),
        total_score=Sum('exam_sessions__total_score', filter=Q(exam_sessions__in=exam_sessions)),
        avg_percentage=Avg('exam_sessions__percentage_score', filter=Q(exam_sessions__in=exam_sessions)),
        total_credit_points=Sum('exam_sessions__credit_points', filter=Q(exam_sessions__in=exam_sessions))
    ).filter(
        total_exams__gt=0  # Only users who have taken exams
    ).order_by('-total_score', '-avg_percentage', '-total_exams')

    # Add rank and badge to each user
    leaderboard_data = []
    for rank, user in enumerate(user_stats, 1):
        # Determine badge based on performance
        avg_score = user.avg_percentage or 0
        total_exams = user.total_exams or 0

        if avg_score >= 95 and total_exams >= 20:
            badge = 'champion'
            badge_label = 'Champion'
        elif avg_score >= 90 and total_exams >= 15:
            badge = 'expert'
            badge_label = 'Expert'
        elif avg_score >= 85 and total_exams >= 10:
            badge = 'master'
            badge_label = 'Master'
        elif avg_score >= 75 and total_exams >= 5:
            badge = 'pro'
            badge_label = 'Pro'
        else:
            badge = 'beginner'
            badge_label = 'Beginner'

        # Determine user title based on performance
        if avg_score >= 95:
            title = 'Quiz Master'
        elif avg_score >= 90:
            title = 'Knowledge Seeker'
        elif avg_score >= 85:
            title = 'Study Enthusiast'
        elif avg_score >= 75:
            title = 'Quick Learner'
        elif avg_score >= 65:
            title = 'Rising Star'
        else:
            title = 'Knowledge Hunter'

        leaderboard_data.append({
            'rank': rank,
            'user': user,
            'title': title,
            'total_score': user.total_score or 0,
            'total_exams': total_exams,
            'avg_percentage': round(avg_score, 1) if avg_score else 0,
            'total_credit_points': user.total_credit_points or 0,
            'badge': badge,
            'badge_label': badge_label,
            'is_current_user': user == request.user
        })

    # Calculate global statistics
    total_users = User.objects.filter(exam_sessions__status='completed').distinct().count()
    active_users_week = User.objects.filter(
        exam_sessions__status='completed',
        exam_sessions__completed_at__gte=now - timedelta(days=7)
    ).distinct().count()
    total_exams_completed = ExamSession.objects.filter(status='completed').count()

    # Find current user's position
    current_user_rank = None
    current_user_data = None
    for item in leaderboard_data:
        if item['is_current_user']:
            current_user_rank = item['rank']
            current_user_data = item
            break

    context = {
        'leaderboard_data': leaderboard_data[:50],  # Top 50 users
        'current_user_rank': current_user_rank,
        'current_user_data': current_user_data,
        'filter_type': filter_type,
        'total_users': total_users,
        'active_users_week': active_users_week,
        'total_exams_completed': total_exams_completed,
    }

    return render(request, 'leaderboard.html', context)


# ============================================================================
# EXAM FUNCTIONALITY
# ============================================================================

@login_required(login_url='auth:signupin')
def start_exam(request, job_id):
    """
    Start a new exam session for a completed processing job
    """
    print(f"DEBUG: start_exam called with job_id={job_id}, user={request.user}")
    try:
        from apps.brain.models import ProcessingJob
        from .models import ExamSession, ShortAnswerEvaluation, ExamAnswer, ExamConfiguration

        # Get the processing job
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)
        print(f"DEBUG: Found job: {job}, status: {job.status}")

        if job.status != 'completed':
            print(f"DEBUG: Job not completed, redirecting to my_quizzes")
            messages.error(request, 'Cannot start exam for incomplete quiz.')
            return redirect('dashboard:my_quizzes')

        # Get questions
        qa_pairs = job.get_qa_pairs()
        print(f"DEBUG: Found {qa_pairs.count()} questions")
        if not qa_pairs.exists():
            print(f"DEBUG: No questions found, redirecting to my_quizzes")
            messages.error(request, 'No questions found for this quiz.')
            return redirect('dashboard:my_quizzes')

        # Get configuration
        config = ExamConfiguration.get_current_config()
        print(f"DEBUG: Got config: {config}")

        # Create new exam session (no attempt restrictions)
        session_id = str(uuid.uuid4())
        questions_list = list(qa_pairs.values_list('id', flat=True))
        random.shuffle(questions_list)  # Randomize question order
        print(f"DEBUG: Created session_id: {session_id}")
        print(f"DEBUG: Questions list: {questions_list}")

        # Get the next attempt number to avoid unique constraint violation
        user_attempts = ExamSession.objects.filter(
            user=request.user,
            processing_job=job
        ).count()
        next_attempt_number = user_attempts + 1
        print(f"DEBUG: Next attempt number: {next_attempt_number}")

        exam_session = ExamSession.objects.create(
            user=request.user,
            processing_job=job,
            session_id=session_id,
            total_questions=len(questions_list),
            time_limit_minutes=len(questions_list) * config.default_time_per_question_minutes,
            allow_navigation=config.allow_question_navigation,
            max_attempts=999,  # Unlimited
            attempt_number=next_attempt_number,
            questions_order=questions_list
        )
        print(f"DEBUG: Created exam session: {exam_session}")
        print(f"DEBUG: Redirecting to exam_session with session_id: {session_id}")

        return redirect('dashboard:exam_session', session_id=session_id)

    except Exception as e:
        print(f"DEBUG: Exception in start_exam: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error starting exam: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def exam_session(request, session_id):
    """
    Display the exam interface for an active session
    """
    print(f"DEBUG: exam_session called with session_id={session_id}, user={request.user}")
    try:
        from .models import ExamSession, ShortAnswerEvaluation, ExamAnswer, ExamAnswer
        from apps.brain.models import QuestionAnswer

        # Get exam session
        exam_session = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        print(f"DEBUG: Found exam session: {exam_session}, status: {exam_session.status}")

        # Check if session is still active
        if exam_session.status != 'active':
            print(f"DEBUG: Session not active (status: {exam_session.status}), redirecting to exam_result")
            return redirect('dashboard:exam_result', session_id=session_id)

        # Check if session has expired
        if exam_session.is_expired():
            print(f"DEBUG: Session expired, marking as expired and redirecting")
            exam_session.status = 'expired'
            exam_session.completed_at = timezone.now()
            exam_session.calculate_score()
            exam_session.save()
            return redirect('dashboard:exam_result', session_id=session_id)

        # Get current question
        current_index = exam_session.current_question_index
        print(f"DEBUG: Current question index: {current_index}, Total questions: {len(exam_session.questions_order)}")
        print(f"DEBUG: Questions order: {exam_session.questions_order}")

        if current_index >= len(exam_session.questions_order):
            # All questions completed
            print(f"DEBUG: All questions completed, marking exam as completed")
            exam_session.status = 'completed'
            exam_session.completed_at = timezone.now()
            exam_session.calculate_score()
            exam_session.save()

            # Send Discord webhook for exam completion
            send_exam_completion_webhook(request.user, exam_session)

            return redirect('dashboard:exam_result', session_id=session_id)

        question_id = exam_session.questions_order[current_index]
        print(f"DEBUG: Getting question with ID: {question_id}")
        current_question = get_object_or_404(QuestionAnswer, id=question_id)
        print(f"DEBUG: Found question: {current_question.question}")

        # Get existing answer if any
        existing_answer = ExamAnswer.objects.filter(
            exam_session=exam_session,
            question=current_question
        ).first()

        # Handle form submission
        if request.method == 'POST':
            user_answer = request.POST.get('answer', '').strip()
            action = request.POST.get('action', 'next')

            if user_answer:
                # For short answer questions, we don't evaluate here - let the frontend handle API evaluation
                if current_question.question_type == 'SHORT':
                    # Just save the answer without evaluation - evaluation will be done via API
                    is_correct = False  # Will be updated when API evaluation completes
                    debug_logs = ["DEBUG: Short answer - evaluation will be done via API"]
                else:
                    # For multiple choice, use the old evaluation method
                    is_correct, debug_logs = evaluate_answer(user_answer, current_question)

                # Print debug logs
                for log in debug_logs:
                    print(log)

                # Save or update answer
                if existing_answer:
                    existing_answer.user_answer = user_answer
                    existing_answer.is_correct = is_correct
                    existing_answer.save()
                else:
                    ExamAnswer.objects.create(
                        exam_session=exam_session,
                        question=current_question,
                        question_index=current_index,
                        user_answer=user_answer,
                        is_correct=is_correct
                    )

            # Handle navigation
            if action == 'next' and current_index < len(exam_session.questions_order) - 1:
                exam_session.current_question_index += 1
                exam_session.save()
            elif action == 'previous' and current_index > 0 and exam_session.allow_navigation:
                exam_session.current_question_index -= 1
                exam_session.save()
            elif action == 'submit':
                exam_session.status = 'completed'
                exam_session.completed_at = timezone.now()
                exam_session.calculate_score()
                exam_session.save()

                # Send Discord webhook for exam completion
                send_exam_completion_webhook(request.user, exam_session)

                return redirect('dashboard:exam_result', session_id=session_id)

            return redirect('dashboard:exam_session', session_id=session_id)

        # Calculate progress percentage
        progress_percentage = ((current_index + 1) / len(exam_session.questions_order)) * 100

        # Prepare context
        context = {
            'exam_session': exam_session,
            'current_question': current_question,
            'current_index': current_index,
            'total_questions': len(exam_session.questions_order),
            'existing_answer': existing_answer,
            'remaining_time': exam_session.get_remaining_time_seconds(),
            'can_go_back': current_index > 0 and exam_session.allow_navigation,
            'can_go_next': current_index < len(exam_session.questions_order) - 1,
            'is_last_question': current_index == len(exam_session.questions_order) - 1,
            'progress_percentage': round(progress_percentage, 1),
        }

        # Use different template for short answer questions
        if current_question.question_type == 'SHORT':
            return render(request, 'short_exam_session.html', context)
        else:
            return render(request, 'exam_session.html', context)

    except Exception as e:
        print(f"DEBUG: Exception in exam_session: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error in exam session: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def submit_exam(request, session_id):
    """
    Submit exam and redirect to results
    """
    try:
        from .models import ExamSession, ShortAnswerEvaluation, ExamAnswer

        exam_session = get_object_or_404(ExamSession, session_id=session_id, user=request.user)

        if exam_session.status == 'active':
            exam_session.status = 'completed'
            exam_session.completed_at = timezone.now()
            exam_session.calculate_score()
            exam_session.save()

            # Send Discord webhook for exam completion
            send_exam_completion_webhook(request.user, exam_session)

        return redirect('dashboard:exam_result', session_id=session_id)

    except Exception as e:
        messages.error(request, f'Error submitting exam: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def exam_result(request, session_id):
    """
    Display exam results
    """
    print(f"DEBUG: exam_result called with session_id={session_id}, user={request.user}")
    try:
        from .models import ExamSession, ShortAnswerEvaluation, ExamAnswer, ExamAnswer

        exam_session = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        print(f"DEBUG: Found exam session: {exam_session}")
        print(f"DEBUG: Exam session status: {exam_session.status}")
        print(f"DEBUG: Exam session completed_at: {exam_session.completed_at}")

        if exam_session.status == 'active':
            print(f"DEBUG: Status is active, redirecting to exam_session")
            return redirect('dashboard:exam_session', session_id=session_id)

        # Get all answers
        print(f"DEBUG: Getting exam answers...")
        answers = ExamAnswer.objects.filter(exam_session=exam_session).order_by('question_index')
        print(f"DEBUG: Found {answers.count()} answers")

        # Check if this is a short answer exam
        is_short_answer_exam = answers.filter(question__question_type='SHORT').exists()
        
        # Get short answer evaluations if applicable
        short_answer_evaluations = []
        if is_short_answer_exam:
            short_answer_evaluations = ShortAnswerEvaluation.objects.filter(
                exam_session=exam_session
            ).order_by('question_index')
            print(f"DEBUG: Found {short_answer_evaluations.count()} short answer evaluations")

        # Debug each answer
        for i, answer in enumerate(answers):
            print(f"DEBUG: Answer {i+1}: Question='{answer.question.question[:50]}...', User='{answer.user_answer}', Correct='{answer.question.answer}', CorrectOption='{answer.question.correct_option}', Type='{answer.question.question_type}', IsCorrect={answer.is_correct}")

        # Calculate detailed statistics
        total_questions = exam_session.total_questions
        answered_questions = answers.count()
        correct_answers = answers.filter(is_correct=True).count()
        incorrect_answers = answered_questions - correct_answers
        print(f"DEBUG: Stats - Total: {total_questions}, Answered: {answered_questions}, Correct: {correct_answers}, Incorrect: {incorrect_answers}")

        # Calculate evaluation summary for short answers
        evaluation_summary = None
        if is_short_answer_exam and short_answer_evaluations.exists():
            total_score = sum(eval.score for eval in short_answer_evaluations)
            max_score = sum(eval.max_score for eval in short_answer_evaluations)
            avg_score = total_score / max_score * 100 if max_score > 0 else 0
            
            # Calculate strengths and weaknesses
            strengths = []
            weaknesses = []
            
            for eval in short_answer_evaluations:
                if eval.accuracy_score >= 7:
                    strengths.append("Accurate answers")
                elif eval.accuracy_score <= 4:
                    weaknesses.append("Accuracy issues")
                
                if eval.completeness_score >= 7:
                    strengths.append("Complete responses")
                elif eval.completeness_score <= 4:
                    weaknesses.append("Incomplete answers")
                
                if eval.clarity_score >= 7:
                    strengths.append("Clear communication")
                elif eval.clarity_score <= 4:
                    weaknesses.append("Unclear explanations")
            
            evaluation_summary = {
                'total_score': total_score,
                'max_score': max_score,
                'average_score': avg_score,
                'strengths': list(set(strengths)),
                'weaknesses': list(set(weaknesses)),
                'suggestions': [
                    "Focus on providing more detailed explanations",
                    "Include specific examples in your answers",
                    "Structure your responses with clear points",
                    "Review the ideal answers for better understanding"
                ]
            }

        context = {
            'exam_session': exam_session,
            'answers': answers,
            'short_answer_evaluations': short_answer_evaluations,
            'is_short_answer_exam': is_short_answer_exam,
            'evaluation_summary': evaluation_summary,
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
            'unanswered_questions': total_questions - answered_questions,
        }

        print(f"DEBUG: Rendering exam_result.html template...")
        return render(request, 'exam_result.html', context)

    except Exception as e:
        print(f"DEBUG: Exception in exam_result: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error displaying exam results: {str(e)}')
        return redirect('dashboard:my_quizzes')


# ============================================================================
# FLASHCARD FUNCTIONALITY
# ============================================================================

@login_required(login_url='auth:signupin')
def start_flashcard(request, job_id):
    """
    Start a new flashcard session for a completed processing job
    """
    try:
        from apps.brain.models import ProcessingJob
        from .models import FlashcardSession, ExamConfiguration

        # Get the processing job
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)

        if job.status != 'completed':
            messages.error(request, 'Cannot start flashcards for incomplete quiz.')
            return redirect('dashboard:my_quizzes')

        # Get questions
        qa_pairs = job.get_qa_pairs()
        if not qa_pairs.exists():
            messages.error(request, 'No questions found for this quiz.')
            return redirect('dashboard:my_quizzes')

        # Get configuration
        config = ExamConfiguration.get_current_config()

        # Create new flashcard session
        session_id = str(uuid.uuid4())
        cards_list = list(qa_pairs.values_list('id', flat=True))
        random.shuffle(cards_list)  # Randomize card order

        flashcard_session = FlashcardSession.objects.create(
            user=request.user,
            processing_job=job,
            session_id=session_id,
            total_cards=len(cards_list),
            time_per_card_seconds=config.default_flashcard_time_seconds,
            auto_advance=config.auto_advance_flashcards,
            cards_order=cards_list
        )

        return redirect('dashboard:flashcard_session', session_id=session_id)

    except Exception as e:
        messages.error(request, f'Error starting flashcards: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def flashcard_session(request, session_id):
    """
    Display the flashcard interface for an active session
    """
    try:
        from .models import FlashcardSession, FlashcardProgress
        from apps.brain.models import QuestionAnswer

        # Get flashcard session
        flashcard_session = get_object_or_404(FlashcardSession, session_id=session_id, user=request.user)

        # Check if session is completed
        if flashcard_session.status != 'active':
            return redirect('dashboard:complete_flashcard', session_id=session_id)

        # Get current card
        current_index = flashcard_session.current_card_index
        if current_index >= len(flashcard_session.cards_order):
            # All cards completed
            flashcard_session.status = 'completed'
            flashcard_session.completed_at = timezone.now()
            flashcard_session.save()
            return redirect('dashboard:complete_flashcard', session_id=session_id)

        card_id = flashcard_session.cards_order[current_index]
        current_card = get_object_or_404(QuestionAnswer, id=card_id)

        # Handle form submission (next card)
        if request.method == 'POST':
            action = request.POST.get('action', 'next')
            was_skipped = action == 'skip'

            # Record progress for current card
            FlashcardProgress.objects.update_or_create(
                flashcard_session=flashcard_session,
                question=current_card,
                defaults={
                    'card_index': current_index,
                    'was_skipped': was_skipped,
                    'time_spent_seconds': 60  # Default time, can be enhanced with JS timing
                }
            )

            # Move to next card
            flashcard_session.current_card_index += 1
            flashcard_session.cards_studied += 1
            flashcard_session.save()

            # Check if this was the last card
            if flashcard_session.current_card_index >= len(flashcard_session.cards_order):
                flashcard_session.status = 'completed'
                flashcard_session.completed_at = timezone.now()
                flashcard_session.save()
                return redirect('dashboard:complete_flashcard', session_id=session_id)

            return redirect('dashboard:flashcard_session', session_id=session_id)

        # Prepare context
        context = {
            'flashcard_session': flashcard_session,
            'current_card': current_card,
            'current_index': current_index,
            'total_cards': len(flashcard_session.cards_order),
            'progress_percentage': ((current_index) / len(flashcard_session.cards_order)) * 100,
            'is_last_card': current_index == len(flashcard_session.cards_order) - 1,
        }

        return render(request, 'flashcard_session.html', context)

    except Exception as e:
        messages.error(request, f'Error in flashcard session: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def complete_flashcard(request, session_id):
    """
    Display flashcard completion page and redirect to exam
    """
    try:
        from .models import FlashcardSession, ExamSession, ExamConfiguration

        flashcard_session = get_object_or_404(FlashcardSession, session_id=session_id, user=request.user)

        if flashcard_session.status == 'active':
            return redirect('dashboard:flashcard_session', session_id=session_id)

        # Check if user wants to start exam
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'start_exam':
                # Get configuration (no attempt restrictions)
                config = ExamConfiguration.get_current_config()

                # Create new exam session (unlimited attempts)
                exam_session_id = str(uuid.uuid4())
                qa_pairs = flashcard_session.processing_job.get_qa_pairs()
                questions_list = list(qa_pairs.values_list('id', flat=True))
                random.shuffle(questions_list)

                ExamSession.objects.create(
                    user=request.user,
                    processing_job=flashcard_session.processing_job,
                    session_id=exam_session_id,
                    total_questions=len(questions_list),
                    time_limit_minutes=len(questions_list) * config.default_time_per_question_minutes,
                    allow_navigation=config.allow_question_navigation,
                    max_attempts=999,  # Unlimited
                    attempt_number=1,  # Always 1 since we don't track attempts
                    questions_order=questions_list
                )

                return redirect('dashboard:exam_session', session_id=exam_session_id)

            elif action == 'back_to_quizzes':
                return redirect('dashboard:my_quizzes')

        # Get progress statistics
        progress_records = flashcard_session.card_progress.all()
        total_time_spent = sum(p.time_spent_seconds for p in progress_records)

        context = {
            'flashcard_session': flashcard_session,
            'total_time_spent': total_time_spent,
            'cards_studied': flashcard_session.cards_studied,
            'total_cards': flashcard_session.total_cards,
            'progress_percentage': flashcard_session.get_progress_percentage(),
        }

        return render(request, 'flashcard_complete.html', context)

    except Exception as e:
        messages.error(request, f'Error completing flashcards: {str(e)}')
        return redirect('dashboard:my_quizzes')


# ============================================================================
# SHORT ANSWER EVALUATION API
# ============================================================================

@login_required(login_url='auth:signupin')
@require_http_methods(["POST"])
@csrf_exempt
def evaluate_short_answer(request):
    """
    Evaluate a single short answer question via API call.
    This endpoint is called for each question as the user progresses through the exam.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        q_id = data.get('q_id')
        user_answer = data.get('user_answer', '').strip()
        
        if not all([session_id, q_id, user_answer]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: session_id, q_id, user_answer'
            }, status=400)
        
        # Get exam session
        exam_session = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        
        if exam_session.status != 'active':
            return JsonResponse({
                'success': False,
                'error': 'Exam session is not active'
            }, status=400)
        
        # Get the question
        from apps.brain.models import QuestionAnswer
        question = get_object_or_404(QuestionAnswer, id=q_id)
        
        if question.question_type != 'SHORT':
            return JsonResponse({
                'success': False,
                'error': 'Question is not a short answer type'
            }, status=400)
        
        # Call API service for evaluation
        api_service = APIService()
        evaluation_result = api_service.evaluate_short_answer(
            exam_id=str(exam_session.id),
            user_id=str(request.user.id),
            q_id=q_id,
            question=question.question,
            user_answer=user_answer
        )
        
        if not evaluation_result['success']:
            return JsonResponse({
                'success': False,
                'error': evaluation_result.get('error', 'Evaluation failed')
            }, status=500)
        
        # Extract evaluation data
        eval_data = evaluation_result['data']
        
        # Save evaluation to database
        evaluation, created = ShortAnswerEvaluation.objects.update_or_create(
            exam_session=exam_session,
            question=question,
            defaults={
                'question_index': exam_session.current_question_index,
                'user_answer': user_answer,
                'score': eval_data.get('score', 0),
                'max_score': eval_data.get('max_score', 10),
                'feedback': eval_data.get('feedback', ''),
                'ideal_answer': eval_data.get('ideal_answer', ''),
                'accuracy_score': eval_data.get('accuracy_score', 0.0),
                'completeness_score': eval_data.get('completeness_score', 0.0),
                'clarity_score': eval_data.get('clarity_score', 0.0),
                'structure_score': eval_data.get('structure_score', 0.0),
                'evaluation_metadata': eval_data.get('metadata', {})
            }
        )
        
        # Also save to ExamAnswer for compatibility
        exam_answer, created = ExamAnswer.objects.update_or_create(
            exam_session=exam_session,
            question=question,
            defaults={
                'question_index': exam_session.current_question_index,
                'user_answer': user_answer,
                'is_correct': evaluation.score >= (evaluation.max_score * 0.6),  # 60% threshold
                'points_earned': evaluation.score,
                'answer_metadata': {
                    'evaluation_id': evaluation.id,
                    'detailed_scores': {
                        'accuracy': evaluation.accuracy_score,
                        'completeness': evaluation.completeness_score,
                        'clarity': evaluation.clarity_score,
                        'structure': evaluation.structure_score
                    }
                }
            }
        )
        
        return JsonResponse({
            'success': True,
            'evaluation': {
                'q_id': q_id,
                'score': evaluation.score,
                'max_score': evaluation.max_score,
                'percentage': evaluation.percentage_score,
                'feedback': evaluation.feedback,
                'ideal_answer': evaluation.ideal_answer,
                'detailed_scores': {
                    'accuracy': evaluation.accuracy_score,
                    'completeness': evaluation.completeness_score,
                    'clarity': evaluation.clarity_score,
                    'structure': evaluation.structure_score
                }
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Evaluation failed: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def store_evaluation_result(request):
    """
    Store evaluation result from external CRM/n8n system.
    This endpoint receives evaluation results and stores them in the database asynchronously.
    """
    try:
        data = json.loads(request.body)
        
        # Extract the evaluation data from the nested structure
        if isinstance(data, list) and len(data) > 0:
            # Handle array format from your example
            evaluation_data = data[0].get('output', {}).get('data', {})
        else:
            # Handle direct object format
            evaluation_data = data.get('data', {})
        
        if not evaluation_data:
            return JsonResponse({
                'success': False,
                'error': 'No evaluation data found in request'
            }, status=400)
        
        # Extract required fields
        q_id = evaluation_data.get('q_id')
        score = evaluation_data.get('score', 0)
        max_score = evaluation_data.get('max_score', 10)
        feedback = evaluation_data.get('feedback', '')
        ideal_answer = evaluation_data.get('ideal_answer', '')
        detailed_scores = evaluation_data.get('detailed_scores', {})
        evaluation_breakdown = evaluation_data.get('evaluation_breakdown', {})
        improvement_suggestions = evaluation_data.get('improvement_suggestions', [])
        metadata = evaluation_data.get('metadata', {})
        
        if not q_id:
            return JsonResponse({
                'success': False,
                'error': 'q_id is required'
            }, status=400)
        
        # Get the question and exam session
        from apps.brain.models import QuestionAnswer
        try:
            question = QuestionAnswer.objects.get(id=q_id)
        except QuestionAnswer.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Question with id {q_id} not found'
            }, status=404)
        
        # Find the exam session (you might need to pass exam_id in the request)
        exam_id = data.get('exam_id') or evaluation_data.get('exam_id')
        if not exam_id:
            return JsonResponse({
                'success': False,
                'error': 'exam_id is required'
            }, status=400)
        
        try:
            exam_session = ExamSession.objects.get(id=exam_id)
        except ExamSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Exam session with id {exam_id} not found'
            }, status=404)
        
        # Get question index from exam session
        question_index = 0
        if q_id in exam_session.questions_order:
            question_index = exam_session.questions_order.index(int(q_id))
        
        # Create or update the evaluation
        evaluation, created = ShortAnswerEvaluation.objects.update_or_create(
            exam_session=exam_session,
            question=question,
            defaults={
                'question_index': question_index,
                'user_answer': evaluation_data.get('user_answer', ''),
                'score': float(score),
                'max_score': int(max_score),
                'feedback': feedback,
                'ideal_answer': ideal_answer,
                'accuracy_score': detailed_scores.get('accuracy', 0.0),
                'completeness_score': detailed_scores.get('completeness', 0.0),
                'clarity_score': detailed_scores.get('clarity', 0.0),
                'structure_score': detailed_scores.get('structure', 0.0),
                'evaluation_metadata': {
                    'evaluation_breakdown': evaluation_breakdown,
                    'improvement_suggestions': improvement_suggestions,
                    'metadata': metadata
                }
            }
        )
        
        # Also update the ExamAnswer for compatibility
        exam_answer, created = ExamAnswer.objects.update_or_create(
            exam_session=exam_session,
            question=question,
            defaults={
                'question_index': question_index,
                'user_answer': evaluation_data.get('user_answer', ''),
                'is_correct': evaluation.percentage_score >= 60,  # 60% threshold
                'points_earned': int(evaluation.score),
                'answer_metadata': {
                    'evaluation_id': evaluation.id,
                    'detailed_scores': detailed_scores,
                    'evaluation_breakdown': evaluation_breakdown,
                    'improvement_suggestions': improvement_suggestions
                }
            }
        )
        
        # Recalculate exam session score
        exam_session.calculate_score()
        
        return JsonResponse({
            'success': True,
            'message': 'Evaluation result stored successfully',
            'evaluation_id': evaluation.id,
            'score': evaluation.score,
            'max_score': evaluation.max_score,
            'percentage': evaluation.percentage_score
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to store evaluation: {str(e)}'
        }, status=500)

@login_required(login_url='auth:signupin')
def give_exam(request):
    """
    Handle the Give Exam request form.
    """
    if request.method == 'POST':
        form = ExamRequestForm(request.POST)
        if form.is_valid():
            exam_request = form.save(commit=False)
            exam_request.user = request.user
            exam_request.save()
            messages.success(request, "Your exam request has been submitted and is pending confirmation.")
            return redirect('dashboard:give_exam')
    else:
        form = ExamRequestForm()
    
    # Get recent requests to show status
    recent_requests = request.user.exam_requests.all().order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'recent_requests': recent_requests
    }
    return render(request, "give_exam.html", context)
