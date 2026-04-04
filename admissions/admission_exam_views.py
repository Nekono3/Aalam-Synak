"""
Admission Exam views – fully independent from the exams app.
Admin: create/edit exams, manage questions, configure subject splits, view results.
Student: start exam, take exam, view results.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import (
    AdmissionExam, AdmissionExamQuestion, AdmissionQuestionOption,
    AdmissionExamSubjectSplit, AdmissionExamAttempt, AdmissionAttemptAnswer,
    AdmissionExamSubjectScore, AdmissionCycle
)
from .admission_exam_forms import (
    AdmissionExamForm, AdmissionExamQuestionForm,
    AdmissionQuestionOptionFormSet, AdmissionExamSubjectSplitFormSet
)


def is_super_admin(user):
    return user.is_authenticated and user.role == 'super_admin'


# ============================================================
# ADMIN VIEWS
# ============================================================

@login_required
@user_passes_test(is_super_admin)
def admission_exam_list(request):
    """List all admission exams."""
    exams = AdmissionExam.objects.select_related('cycle', 'created_by').all()
    return render(request, 'admissions/admission_exam_list.html', {'exams': exams})


@login_required
@user_passes_test(is_super_admin)
def admission_exam_create(request):
    """Create a new admission exam."""
    if request.method == 'POST':
        form = AdmissionExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, _('Admission exam created successfully.'))
            return redirect('admissions:admission_exam_questions', pk=exam.pk)
    else:
        form = AdmissionExamForm()
    return render(request, 'admissions/admission_exam_form.html', {'form': form})


@login_required
@user_passes_test(is_super_admin)
def admission_exam_edit(request, pk):
    """Edit an existing admission exam."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    if request.method == 'POST':
        form = AdmissionExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, _('Admission exam updated successfully.'))
            return redirect('admissions:admission_exam_list')
    else:
        form = AdmissionExamForm(instance=exam)
    return render(request, 'admissions/admission_exam_form.html', {
        'form': form, 'exam': exam, 'is_edit': True
    })


@login_required
@user_passes_test(is_super_admin)
def admission_exam_questions(request, pk):
    """View and manage questions for an admission exam."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    questions = exam.admission_questions.prefetch_related('options').all()
    return render(request, 'admissions/admission_exam_questions.html', {
        'exam': exam, 'questions': questions
    })


@login_required
@user_passes_test(is_super_admin)
def admission_exam_add_question(request, pk):
    """Add a question to an admission exam."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    
    if request.method == 'POST':
        form = AdmissionExamQuestionForm(request.POST, request.FILES)
        formset = AdmissionQuestionOptionFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            if not question.order:
                last_order = exam.admission_questions.order_by('-order').values_list('order', flat=True).first()
                question.order = (last_order or 0) + 1
            question.save()
            
            formset.instance = question
            formset.save()
            
            messages.success(request, _('Question added successfully.'))
            return redirect('admissions:admission_exam_questions', pk=exam.pk)
    else:
        form = AdmissionExamQuestionForm()
        formset = AdmissionQuestionOptionFormSet()
    
    return render(request, 'admissions/admission_exam_question_form.html', {
        'exam': exam, 'form': form, 'formset': formset
    })


@login_required
@user_passes_test(is_super_admin)
def admission_exam_edit_question(request, pk, question_pk):
    """Edit an existing question."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    question = get_object_or_404(AdmissionExamQuestion, pk=question_pk, exam=exam)
    
    if request.method == 'POST':
        form = AdmissionExamQuestionForm(request.POST, request.FILES, instance=question)
        formset = AdmissionQuestionOptionFormSet(request.POST, instance=question)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _('Question updated successfully.'))
            return redirect('admissions:admission_exam_questions', pk=exam.pk)
    else:
        form = AdmissionExamQuestionForm(instance=question)
        formset = AdmissionQuestionOptionFormSet(instance=question)
    
    return render(request, 'admissions/admission_exam_question_form.html', {
        'exam': exam, 'form': form, 'formset': formset,
        'question': question, 'is_edit': True
    })


@login_required
@user_passes_test(is_super_admin)
def admission_exam_delete_question(request, pk, question_pk):
    """Delete a question from an admission exam."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    question = get_object_or_404(AdmissionExamQuestion, pk=question_pk, exam=exam)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, _('Question deleted.'))
        return redirect('admissions:admission_exam_questions', pk=exam.pk)
    
    return render(request, 'admissions/admission_exam_question_delete.html', {
        'exam': exam, 'question': question
    })


@login_required
@user_passes_test(is_super_admin)
def admission_exam_subject_splits(request, pk):
    """Configure subject ranges for an admission exam."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    
    if request.method == 'POST':
        formset = AdmissionExamSubjectSplitFormSet(request.POST, instance=exam)
        if formset.is_valid():
            formset.save()
            messages.success(request, _('Subject splits saved successfully.'))
            return redirect('admissions:admission_exam_questions', pk=exam.pk)
    else:
        formset = AdmissionExamSubjectSplitFormSet(instance=exam)
    
    return render(request, 'admissions/admission_exam_subject_splits.html', {
        'exam': exam, 'formset': formset
    })


@login_required
@user_passes_test(is_super_admin)
def admission_exam_results(request, pk):
    """View all attempts/results for an admission exam."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    attempts = exam.attempts.select_related('student').prefetch_related('subject_scores').all()
    
    return render(request, 'admissions/admission_exam_results.html', {
        'exam': exam, 'attempts': attempts
    })


# ============================================================
# STUDENT VIEWS
# ============================================================

@login_required
def admission_exam_start(request, pk):
    """Start an admission exam attempt."""
    exam = get_object_or_404(AdmissionExam, pk=pk)
    
    # Check if already attempted
    existing = AdmissionExamAttempt.objects.filter(exam=exam, student=request.user).first()
    if existing:
        if existing.status == 'completed':
            messages.info(request, _('You have already completed this exam.'))
            return redirect('admissions:admission_exam_result', attempt_pk=existing.pk)
        # Resume in-progress attempt
        return redirect('admissions:admission_exam_take', attempt_pk=existing.pk)
    
    # Check availability
    if not exam.is_available:
        messages.error(request, _('This exam is not currently available.'))
        return redirect('admissions:student_admission')
    
    # Create attempt
    if request.method == 'POST':
        attempt = AdmissionExamAttempt.objects.create(
            exam=exam,
            student=request.user
        )
        return redirect('admissions:admission_exam_take', attempt_pk=attempt.pk)
    
    return render(request, 'admissions/admission_exam_start.html', {'exam': exam})


@login_required
def admission_exam_take(request, attempt_pk):
    """Take an admission exam (render questions, handle answers)."""
    attempt = get_object_or_404(
        AdmissionExamAttempt.objects.select_related('exam'),
        pk=attempt_pk, student=request.user
    )
    
    # Check locked or completed
    if attempt.status in ('completed', 'locked', 'timed_out'):
        return redirect('admissions:admission_exam_result', attempt_pk=attempt.pk)
    
    # Check time
    if attempt.time_remaining <= 0:
        attempt.status = 'timed_out'
        attempt.finished_at = timezone.now()
        attempt.save(update_fields=['status', 'finished_at'])
        attempt.calculate_score()
        return redirect('admissions:admission_exam_result', attempt_pk=attempt.pk)
    
    exam = attempt.exam
    questions = list(exam.admission_questions.prefetch_related('options').order_by('order', 'id'))
    
    # Get existing answers
    existing_answers = {
        a.question_id: a.selected_option_id
        for a in attempt.admission_answers.all()
    }
    
    # Mark answered questions
    for q in questions:
        q.selected_option_id = existing_answers.get(q.pk)
    
    context = {
        'attempt': attempt,
        'exam': exam,
        'questions': questions,
        'time_remaining': attempt.time_remaining,
        'enable_tab_warnings': exam.enable_tab_warnings,
        'max_tab_switches': exam.max_tab_switches,
    }
    return render(request, 'admissions/admission_take_exam.html', context)


@login_required
@require_POST
def admission_exam_save_answer(request, attempt_pk):
    """AJAX: Save a single answer during exam."""
    attempt = get_object_or_404(
        AdmissionExamAttempt, pk=attempt_pk, student=request.user
    )
    
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'Exam not in progress'}, status=400)
    
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        option_id = data.get('option_id')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid data'}, status=400)
    
    question = get_object_or_404(AdmissionExamQuestion, pk=question_id, exam=attempt.exam)
    option = get_object_or_404(AdmissionQuestionOption, pk=option_id, question=question) if option_id else None
    
    answer, created = AdmissionAttemptAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={'selected_option': option}
    )
    
    return JsonResponse({'status': 'saved', 'is_correct': answer.is_correct})


@login_required
@require_POST
def admission_exam_tab_switch(request, attempt_pk):
    """AJAX: Record a tab switch event."""
    attempt = get_object_or_404(
        AdmissionExamAttempt, pk=attempt_pk, student=request.user
    )
    
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'Exam not in progress'}, status=400)
    
    if not attempt.exam.enable_tab_warnings:
        return JsonResponse({'status': 'ok', 'warnings_disabled': True})
    
    attempt.tab_switch_count += 1
    
    if attempt.tab_switch_count >= attempt.exam.max_tab_switches:
        attempt.is_locked = True
        attempt.status = 'locked'
        attempt.lock_reason = _('Too many tab switches')
        attempt.finished_at = timezone.now()
        attempt.save()
        attempt.calculate_score()
        return JsonResponse({'status': 'locked', 'count': attempt.tab_switch_count})
    
    attempt.save(update_fields=['tab_switch_count'])
    return JsonResponse({
        'status': 'warning',
        'count': attempt.tab_switch_count,
        'remaining': attempt.exam.max_tab_switches - attempt.tab_switch_count
    })


@login_required
@require_POST
def admission_exam_submit(request, attempt_pk):
    """Submit an admission exam attempt."""
    attempt = get_object_or_404(
        AdmissionExamAttempt, pk=attempt_pk, student=request.user
    )
    
    if attempt.status != 'in_progress':
        return redirect('admissions:admission_exam_result', attempt_pk=attempt.pk)
    
    attempt.status = 'completed'
    attempt.finished_at = timezone.now()
    attempt.save(update_fields=['status', 'finished_at'])
    attempt.calculate_score()
    
    return redirect('admissions:admission_exam_result', attempt_pk=attempt.pk)


@login_required
def admission_exam_result(request, attempt_pk):
    """View results of an admission exam attempt."""
    attempt = get_object_or_404(
        AdmissionExamAttempt.objects.select_related('exam', 'student'),
        pk=attempt_pk
    )
    
    # Only allow the student or admin to see results
    if request.user != attempt.student and request.user.role != 'super_admin':
        messages.error(request, _('You do not have permission to view this result.'))
        return redirect('accounts:dashboard')
    
    subject_scores = attempt.subject_scores.all()
    
    # Get answer details for admin view
    answers = None
    if request.user.role == 'super_admin':
        answers = attempt.admission_answers.select_related(
            'question', 'selected_option'
        ).order_by('question__order')
    
    context = {
        'attempt': attempt,
        'exam': attempt.exam,
        'subject_scores': subject_scores,
        'answers': answers,
    }
    return render(request, 'admissions/admission_exam_result.html', context)
