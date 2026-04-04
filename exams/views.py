from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
import json
import random

from accounts.decorators import role_required
from schools.models import School, Subject
from .models import (
    OnlineExam, ExamQuestion, QuestionOption, MatchingPair, OrderingItem,
    ExamAttempt, AttemptAnswer, ProctorEvent
)
from .forms import OnlineExamForm, ExamQuestionForm, QuestionOptionFormSet, MatchingPairFormSet, OrderingItemFormSet


# ============================================
# TEACHER/ADMIN VIEWS
# ============================================

@login_required
@role_required(['super_admin', 'teacher'])
def exam_list_view(request):
    """List all online exams."""
    from schools.models import SchoolClass
    
    exams = OnlineExam.objects.select_related('subject', 'school', 'created_by')
    
    # Filter by school for teachers
    if request.user.is_teacher and request.user.primary_school:
        exams = exams.filter(school=request.user.primary_school)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        exams = exams.filter(
            Q(title__icontains=search) |
            Q(subject__name__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    now = timezone.now()
    if status == 'active':
        exams = exams.filter(is_active=True, start_time__lte=now, end_time__gte=now)
    elif status == 'upcoming':
        exams = exams.filter(start_time__gt=now)
    elif status == 'ended':
        exams = exams.filter(end_time__lt=now)
    
    # Filter by class
    class_id = request.GET.get('class_id', '')
    if class_id:
        exams = exams.filter(target_classes__id=class_id).distinct()
    
    # Get available classes for the filter dropdown
    available_classes = SchoolClass.objects.all().order_by('grade', 'section')
    
    paginator = Paginator(exams, 20)
    page = request.GET.get('page', 1)
    exams = paginator.get_page(page)
    
    return render(request, 'exams/exam_list.html', {
        'exams': exams,
        'search': search,
        'status': status,
        'class_id': class_id,
        'available_classes': available_classes,
    })


@login_required
@role_required(['super_admin', 'teacher'])
def exam_create_view(request):
    """Create a new online exam."""
    if request.method == 'POST':
        form = OnlineExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            form.save_m2m()  # Save target_classes M2M
            messages.success(request, _('Exam created successfully. Now add questions.'))
            return redirect('exams:exam_questions', pk=exam.pk)
    else:
        form = OnlineExamForm()
    
    schools = School.objects.filter(is_active=True)
    subjects = Subject.objects.all()
    
    return render(request, 'exams/exam_form.html', {
        'form': form,
        'schools': schools,
        'subjects': subjects,
        'is_edit': False,
    })


@login_required
@role_required(['super_admin', 'teacher'])
def exam_edit_view(request, pk):
    """Edit an existing exam."""
    exam = get_object_or_404(OnlineExam, pk=pk)
    
    if request.method == 'POST':
        form = OnlineExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, _('Exam updated successfully.'))
            return redirect('exams:exam_list')
    else:
        form = OnlineExamForm(instance=exam)
    
    schools = School.objects.filter(is_active=True)
    subjects = Subject.objects.all()
    
    return render(request, 'exams/exam_form.html', {
        'form': form,
        'exam': exam,
        'schools': schools,
        'subjects': subjects,
        'is_edit': True,
    })


@login_required
@role_required(['super_admin', 'teacher'])
def exam_delete_view(request, pk):
    """Delete an exam."""
    exam = get_object_or_404(OnlineExam, pk=pk)
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, _('Exam deleted successfully.'))
        return redirect('exams:exam_list')
    
    return render(request, 'exams/exam_confirm_delete.html', {'exam': exam})


@login_required
@role_required(['super_admin', 'teacher'])
def exam_questions_view(request, pk):
    """Manage questions for an exam."""
    exam = get_object_or_404(OnlineExam, pk=pk)
    questions = exam.questions.prefetch_related('options').all()
    
    return render(request, 'exams/exam_questions.html', {
        'exam': exam,
        'questions': questions,
    })


@login_required
@role_required(['super_admin', 'teacher'])
def add_question_view(request, exam_pk):
    """Add a question to an exam."""
    exam = get_object_or_404(OnlineExam, pk=exam_pk)
    
    if request.method == 'POST':
        form = ExamQuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.order = exam.questions.count() + 1
            question.save()
            
            if question.question_type == 'fill_blanks' or question.question_type == 'true_false':
                messages.success(request, _('Question added successfully.'))
                return redirect('exams:exam_questions', pk=exam.pk)
            
            if question.question_type == 'matching':
                matching_formset = MatchingPairFormSet(request.POST, instance=question)
                if matching_formset.is_valid():
                    matching_formset.save()
                    messages.success(request, _('Matching question added successfully.'))
                    return redirect('exams:exam_questions', pk=exam.pk)
                else:
                    question.delete()
                    form = ExamQuestionForm(request.POST, request.FILES)
                    formset = QuestionOptionFormSet()
                    matching_formset = MatchingPairFormSet(request.POST)
                    ordering_formset = OrderingItemFormSet()
                    return render(request, 'exams/question_form.html', {
                        'exam': exam, 'form': form, 'formset': formset,
                        'matching_formset': matching_formset, 'ordering_formset': ordering_formset,
                        'is_edit': False,
                    })
            
            if question.question_type == 'ordering':
                ordering_formset = OrderingItemFormSet(request.POST, instance=question)
                if ordering_formset.is_valid():
                    ordering_formset.save()
                    messages.success(request, _('Ordering question added successfully.'))
                    return redirect('exams:exam_questions', pk=exam.pk)
                else:
                    question.delete()
                    form = ExamQuestionForm(request.POST, request.FILES)
                    formset = QuestionOptionFormSet()
                    matching_formset = MatchingPairFormSet()
                    ordering_formset = OrderingItemFormSet(request.POST)
                    return render(request, 'exams/question_form.html', {
                        'exam': exam, 'form': form, 'formset': formset,
                        'matching_formset': matching_formset, 'ordering_formset': ordering_formset,
                        'is_edit': False,
                    })
            
            # Multiple choice
            formset = QuestionOptionFormSet(request.POST, instance=question)
            if formset.is_valid():
                formset.save()
                messages.success(request, _('Question added successfully.'))
                return redirect('exams:exam_questions', pk=exam.pk)
            else:
                question.delete()
        else:
            formset = QuestionOptionFormSet(request.POST)
    else:
        form = ExamQuestionForm()
        formset = QuestionOptionFormSet()
    
    matching_formset = MatchingPairFormSet()
    ordering_formset = OrderingItemFormSet()
    
    return render(request, 'exams/question_form.html', {
        'exam': exam,
        'form': form,
        'formset': formset,
        'matching_formset': matching_formset,
        'ordering_formset': ordering_formset,
        'is_edit': False,
    })


@login_required
@role_required(['super_admin', 'teacher'])
def edit_question_view(request, pk):
    """Edit a question."""
    question = get_object_or_404(ExamQuestion, pk=pk)
    exam = question.exam
    
    if request.method == 'POST':
        form = ExamQuestionForm(request.POST, request.FILES, instance=question)
        formset = QuestionOptionFormSet(request.POST, instance=question)
        matching_formset = MatchingPairFormSet(request.POST, instance=question)
        ordering_formset = OrderingItemFormSet(request.POST, instance=question)
        
        if form.is_valid():
            saved_question = form.save()
            
            if saved_question.question_type == 'fill_blanks' or saved_question.question_type == 'true_false':
                messages.success(request, _('Question updated successfully.'))
                return redirect('exams:exam_questions', pk=exam.pk)
            elif saved_question.question_type == 'matching':
                if matching_formset.is_valid():
                    matching_formset.save()
                    messages.success(request, _('Question updated successfully.'))
                    return redirect('exams:exam_questions', pk=exam.pk)
            elif saved_question.question_type == 'ordering':
                if ordering_formset.is_valid():
                    ordering_formset.save()
                    messages.success(request, _('Question updated successfully.'))
                    return redirect('exams:exam_questions', pk=exam.pk)
            else:  # multiple_choice
                if formset.is_valid():
                    formset.save()
                    messages.success(request, _('Question updated successfully.'))
                    return redirect('exams:exam_questions', pk=exam.pk)
    else:
        form = ExamQuestionForm(instance=question)
        formset = QuestionOptionFormSet(instance=question)
        matching_formset = MatchingPairFormSet(instance=question)
        ordering_formset = OrderingItemFormSet(instance=question)
    
    return render(request, 'exams/question_form.html', {
        'exam': exam,
        'question': question,
        'form': form,
        'formset': formset,
        'matching_formset': matching_formset,
        'ordering_formset': ordering_formset,
        'is_edit': True,
    })


@login_required
@role_required(['super_admin', 'teacher'])
def delete_question_view(request, pk):
    """Delete a question."""
    question = get_object_or_404(ExamQuestion, pk=pk)
    exam = question.exam
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, _('Question deleted.'))
        return redirect('exams:exam_questions', pk=exam.pk)
    
    return render(request, 'exams/question_confirm_delete.html', {
        'question': question,
        'exam': exam,
    })


@login_required
@role_required(['super_admin', 'teacher'])
def exam_results_view(request, pk):
    """View all attempts/results for an exam."""
    exam = get_object_or_404(OnlineExam, pk=pk)
    attempts = exam.attempts.select_related('student').order_by('-started_at')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'locked':
        attempts = attempts.filter(is_locked=True)
    elif status == 'completed':
        attempts = attempts.filter(status='completed')
    elif status == 'in_progress':
        attempts = attempts.filter(status='in_progress')
    
    # Search by name or email
    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        attempts = attempts.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__email__icontains=search)
        )
    
    # Sort by score
    sort = request.GET.get('sort', '')
    if sort == 'score_high':
        attempts = attempts.order_by('-percentage', '-score')
    elif sort == 'score_low':
        attempts = attempts.order_by('percentage', 'score')
    
    return render(request, 'exams/exam_results.html', {
        'exam': exam,
        'attempts': attempts,
        'status': status,
        'search': search,
        'sort': sort,
    })


@login_required
@role_required(['super_admin'])
def unlock_attempt_view(request, pk):
    """Admin unlock a locked exam attempt."""
    attempt = get_object_or_404(ExamAttempt, pk=pk)
    
    if request.method == 'POST':
        # Reset the attempt
        attempt.is_locked = False
        attempt.status = 'in_progress'
        attempt.tab_switch_count = 0
        attempt.lock_reason = ''
        attempt.started_at = timezone.now()  # Reset timer
        attempt.save()
        
        # Delete previous answers
        attempt.answers.all().delete()
        
        # Log unlock event
        ProctorEvent.objects.create(
            attempt=attempt,
            event_type='admin_unlock',
            details={'unlocked_by': request.user.email}
        )
        
        messages.success(request, _('Attempt unlocked. Student can retake the exam.'))
        return redirect('exams:exam_results', pk=attempt.exam.pk)
    
    return render(request, 'exams/unlock_confirm.html', {'attempt': attempt})


@login_required
@role_required(['super_admin', 'teacher'])
def view_attempt_answers_view(request, pk):
    """View detailed answers for a specific exam attempt."""
    attempt = get_object_or_404(ExamAttempt, pk=pk)
    exam = attempt.exam
    answers = attempt.answers.select_related('question', 'selected_option').order_by('question__order')
    
    return render(request, 'exams/attempt_answers.html', {
        'attempt': attempt,
        'exam': exam,
        'answers': answers,
    })


# ============================================
# STUDENT VIEWS
# ============================================

@login_required
def student_exams_view(request):
    """List available exams for student."""
    now = timezone.now()
    
    # Get exams available for student's school
    exams = OnlineExam.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    )
    
    if request.user.primary_school:
        exams = exams.filter(school=request.user.primary_school)
    
    # Filter by target classes: show exams that target the student's class
    # or exams with no class restriction (empty target_classes)
    from django.db.models import Count
    if request.user.school_class:
        # Annotate to find exams with no target classes (available to all)
        exams = exams.annotate(
            class_count=Count('target_classes')
        ).filter(
            Q(class_count=0) |
            Q(target_classes=request.user.school_class)
        ).distinct()
    else:
        # Student with no class sees only non-class-restricted exams
        exams = exams.annotate(
            class_count=Count('target_classes')
        ).filter(class_count=0)
    
    # Get student's attempts
    attempts = {
        a.exam_id: a 
        for a in ExamAttempt.objects.filter(student=request.user)
    }
    
    exams_data = []
    for exam in exams:
        attempt = attempts.get(exam.pk)
        exams_data.append({
            'exam': exam,
            'attempt': attempt,
            'can_start': attempt is None or (attempt.is_locked and False),  # Only one attempt
            'is_completed': attempt and attempt.status == 'completed',
            'is_locked': attempt and attempt.is_locked,
        })
    
    return render(request, 'exams/student_exams.html', {
        'exams_data': exams_data,
    })


@login_required
def start_exam_view(request, pk):
    """Start an exam attempt."""
    exam = get_object_or_404(OnlineExam, pk=pk)
    
    # Check if exam is available
    if not exam.is_available:
        messages.error(request, _('This exam is not currently available.'))
        return redirect('exams:student_exams')
    
    # Check for existing attempt
    existing = ExamAttempt.objects.filter(exam=exam, student=request.user).first()
    if existing:
        if existing.is_locked:
            messages.error(request, _('Your exam is locked. Contact admin to unlock.'))
            return redirect('exams:student_exams')
        elif existing.status == 'completed':
            messages.info(request, _('You have already completed this exam.'))
            return redirect('exams:exam_result', pk=existing.pk)
        else:
            # Continue existing attempt
            return redirect('exams:take_exam', pk=existing.pk)
    
    # Create new attempt
    attempt = ExamAttempt.objects.create(
        exam=exam,
        student=request.user,
        status='in_progress'
    )
    
    # Log start event
    ProctorEvent.objects.create(
        attempt=attempt,
        event_type='exam_started'
    )
    
    return redirect('exams:take_exam', pk=attempt.pk)


@login_required
def take_exam_view(request, pk):
    """Main exam-taking interface with proctoring."""
    attempt = get_object_or_404(ExamAttempt, pk=pk, student=request.user)
    
    # Check if locked
    if attempt.is_locked:
        messages.error(request, _('This exam has been locked due to suspicious activity.'))
        return redirect('exams:student_exams')
    
    # Check if completed
    if attempt.status == 'completed':
        return redirect('exams:exam_result', pk=attempt.pk)
    
    # Check if timed out
    if attempt.time_remaining <= 0:
        attempt.status = 'timed_out'
        attempt.finished_at = timezone.now()
        attempt.calculate_score()
        messages.warning(request, _('Time expired. Your exam has been submitted.'))
        return redirect('exams:exam_result', pk=attempt.pk)
    
    exam = attempt.exam
    questions = list(exam.questions.prefetch_related('options', 'matching_pairs', 'ordering_items').all())
    
    # Shuffle if needed
    if exam.shuffle_questions:
        random.shuffle(questions)
    
    # Get existing answers for multiple choice
    existing_answers = {
        a.question_id: a.selected_option_id
        for a in attempt.answers.all()
        if a.selected_option_id
    }
    
    # Get existing text answers for fill_blanks and true_false
    existing_text_answers = {
        a.question_id: a.text_answer
        for a in attempt.answers.all()
        if a.text_answer
    }
    
    # Get existing matching answers
    existing_matching_answers = {
        a.question_id: a.matching_answers
        for a in attempt.answers.all()
        if a.matching_answers
    }
    
    # Get existing ordering answers
    existing_ordering_answers = {
        a.question_id: a.ordering_answers
        for a in attempt.answers.all()
        if a.ordering_answers
    }
    
    return render(request, 'exams/take_exam.html', {
        'attempt': attempt,
        'exam': exam,
        'questions': questions,
        'existing_answers': existing_answers,
        'existing_answers_json': json.dumps({str(k): v for k, v in existing_answers.items()}),
        'existing_text_answers': existing_text_answers,
        'existing_matching_answers': json.dumps(existing_matching_answers),
        'existing_ordering_answers': json.dumps(existing_ordering_answers),
        'time_remaining': attempt.time_remaining,
    })


@login_required
@require_POST
def save_answer_view(request, attempt_pk):
    """Save an answer via AJAX."""
    attempt = get_object_or_404(ExamAttempt, pk=attempt_pk, student=request.user)
    
    if attempt.is_locked or attempt.status != 'in_progress':
        return JsonResponse({'error': 'Exam is not active'}, status=400)
    
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        option_id = data.get('option_id')
        text_answer = data.get('text_answer', '')
        
        question = get_object_or_404(ExamQuestion, pk=question_id, exam=attempt.exam)
        
        # Handle different question types
        if question.question_type == 'fill_blanks':
            # Text-based answer
            answer, created = AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'text_answer': text_answer,
                    'selected_option': None
                }
            )
        elif question.question_type == 'matching':
            # Matching answer — JSON pairs
            matching_data = data.get('matching_answers', {})
            answer, created = AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'matching_answers': matching_data,
                    'selected_option': None,
                    'text_answer': ''
                }
            )
        elif question.question_type == 'ordering':
            # Ordering answer — JSON positions
            ordering_data = data.get('ordering_answers', {})
            answer, created = AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'ordering_answers': ordering_data,
                    'selected_option': None,
                    'text_answer': ''
                }
            )
        elif question.question_type == 'true_false':
            # True/False answer — stored as text "true" or "false"
            answer, created = AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'text_answer': text_answer,
                    'selected_option': None
                }
            )
        else:
            # Option-based answer (multiple_choice)
            option = get_object_or_404(QuestionOption, pk=option_id, question=question) if option_id else None
            answer, created = AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_option': option,
                    'text_answer': ''
                }
            )
        
        return JsonResponse({'success': True, 'is_correct': answer.is_correct})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def log_proctor_event_view(request, attempt_pk):
    """Log a proctoring event via AJAX."""
    attempt = get_object_or_404(ExamAttempt, pk=attempt_pk, student=request.user)
    
    if attempt.status != 'in_progress':
        return JsonResponse({'locked': attempt.is_locked})
    
    try:
        data = json.loads(request.body)
        event_type = data.get('event_type')
        
        # Log the event
        ProctorEvent.objects.create(
            attempt=attempt,
            event_type=event_type,
            details=data.get('details', {})
        )
        
        # Handle tab switches
        if event_type in ['tab_switch', 'window_blur']:
            attempt.tab_switch_count += 1
            
            if attempt.tab_switch_count >= attempt.exam.max_tab_switches:
                attempt.is_locked = True
                attempt.status = 'locked'
                attempt.lock_reason = _('Too many tab switches')
                attempt.finished_at = timezone.now()
                attempt.calculate_score()
                
                ProctorEvent.objects.create(
                    attempt=attempt,
                    event_type='exam_locked',
                    details={'reason': 'max_tab_switches', 'count': attempt.tab_switch_count}
                )
            
            attempt.save()
        
        return JsonResponse({
            'success': True,
            'tab_count': attempt.tab_switch_count,
            'max_allowed': attempt.exam.max_tab_switches,
            'locked': attempt.is_locked
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def submit_exam_view(request, pk):
    """Submit the completed exam."""
    attempt = get_object_or_404(ExamAttempt, pk=pk, student=request.user)
    
    if attempt.is_locked:
        return redirect('exams:student_exams')
    
    if attempt.status == 'completed':
        return redirect('exams:exam_result', pk=attempt.pk)
    
    # Mark as completed
    attempt.status = 'completed'
    attempt.finished_at = timezone.now()
    attempt.calculate_score()
    
    # Log submission
    ProctorEvent.objects.create(
        attempt=attempt,
        event_type='exam_submitted'
    )
    
    messages.success(request, _('Exam submitted successfully!'))
    return redirect('exams:exam_result', pk=attempt.pk)


@login_required
def exam_result_view(request, pk):
    """View exam result."""
    attempt = get_object_or_404(ExamAttempt, pk=pk, student=request.user)
    
    if attempt.status == 'in_progress' and not attempt.is_locked:
        return redirect('exams:take_exam', pk=attempt.pk)
    
    exam = attempt.exam
    
    # Get answers with details if results are shown
    answers = None
    if exam.show_results_immediately or request.user.is_super_admin:
        answers = attempt.answers.select_related(
            'question', 'selected_option'
        ).prefetch_related('question__options')
    
    return render(request, 'exams/exam_result.html', {
        'attempt': attempt,
        'exam': exam,
        'answers': answers,
    })


@login_required
@require_POST
def upload_recording_view(request, attempt_pk):
    """Upload exam recording video."""
    attempt = get_object_or_404(ExamAttempt, pk=attempt_pk, student=request.user)
    
    video_file = request.FILES.get('recording')
    if video_file:
        # Save with a descriptive filename
        from django.core.files.base import ContentFile
        filename = f"exam_{attempt.exam.pk}_student_{request.user.pk}_{attempt.pk}.webm"
        attempt.recording.save(filename, video_file, save=True)
        return JsonResponse({'status': 'ok'})
    
    return JsonResponse({'status': 'error', 'message': 'No recording file provided'}, status=400)


@login_required
@role_required(['super_admin', 'teacher'])
@require_POST
def delete_recording_view(request, pk):
    """Delete a recording file from an exam attempt."""
    attempt = get_object_or_404(ExamAttempt, pk=pk)
    
    if attempt.recording:
        attempt.recording.delete(save=True)
        messages.success(request, _('Recording deleted successfully.'))
    else:
        messages.warning(request, _('No recording found for this attempt.'))
    
    return redirect('exams:exam_results', pk=attempt.exam.pk)


# ============ Teacher Management Views ============

@login_required
@role_required(['teacher', 'super_admin'])
def teacher_exam_list_view(request):
    """Teacher management - List exams for teacher's school (read-only)."""
    school = request.user.primary_school
    
    exams = OnlineExam.objects.all().order_by('-created_at')
    
    if school and request.user.role == 'teacher':
        exams = exams.filter(school=school)
    elif request.user.role == 'super_admin':
        school_filter = request.GET.get('school')
        if school_filter:
            exams = exams.filter(school_id=school_filter)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        exams = exams.filter(Q(title__icontains=search))
    
    paginator = Paginator(exams, 20)
    page = request.GET.get('page', 1)
    exams = paginator.get_page(page)
    
    schools = School.objects.filter(is_active=True) if request.user.role == 'super_admin' else None
    
    return render(request, 'exams/teacher_exam_list.html', {
        'exams': exams,
        'search': search,
        'school': school,
        'schools': schools,
    })


@login_required
@role_required(['teacher', 'super_admin'])
def teacher_exam_results_view(request, pk):
    """Teacher management - View exam results with student search."""
    exam = get_object_or_404(OnlineExam, pk=pk)
    
    # Teachers can only see exams from their school
    if request.user.role == 'teacher' and request.user.primary_school:
        if exam.school != request.user.primary_school:
            messages.error(request, _('You do not have access to this exam.'))
            return redirect('exams:teacher_exam_list')
    
    attempts = ExamAttempt.objects.filter(
        exam=exam
    ).select_related('student').order_by('-submitted_at')
    
    # Search by student name
    search = request.GET.get('search', '')
    if search:
        attempts = attempts.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__email__icontains=search)
        )
    
    # Stats
    completed_attempts = attempts.filter(status='completed')
    total_attempts = completed_attempts.count()
    avg_score = None
    if total_attempts > 0:
        from django.db.models import Avg
        avg_result = completed_attempts.aggregate(avg=Avg('score_percentage'))
        avg_score = round(avg_result['avg'], 1) if avg_result['avg'] else None
    
    paginator = Paginator(attempts, 50)
    page = request.GET.get('page', 1)
    attempts = paginator.get_page(page)
    
    return render(request, 'exams/teacher_exam_results.html', {
        'exam': exam,
        'attempts': attempts,
        'search': search,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
    })
