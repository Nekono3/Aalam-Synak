from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    # Admin Views
    path('', views.admission_dashboard, name='dashboard'),
    path('cycles/', views.cycle_list, name='cycle_list'),
    path('cycles/create/', views.cycle_create, name='cycle_create'),
    path('cycles/<int:pk>/edit/', views.cycle_edit, name='cycle_edit'),
    path('cycles/<int:pk>/questions/', views.cycle_questions, name='cycle_questions'),
    path('cycles/<int:pk>/questions/add/', views.cycle_add_question, name='cycle_add_question'),
    path('cycles/<int:pk>/questions/<int:question_pk>/edit/', views.cycle_edit_question, name='cycle_edit_question'),
    path('cycles/<int:pk>/questions/<int:question_pk>/delete/', views.cycle_delete_question, name='cycle_delete_question'),
    path('cycles/<int:pk>/splits/', views.cycle_subject_splits, name='cycle_subject_splits'),
    path('registry/', views.school_registry, name='school_registry'),
    path('registry/new/', views.external_school_create, name='external_school_create'),
    path('registry/<int:pk>/delete/', views.external_school_delete, name='external_school_delete'),
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('analytics/', views.admission_analytics, name='admission_analytics'),
    path('analytics/upload/', views.admission_analytics_upload, name='admission_analytics_upload'),
    path('analytics/dashboard/', views.admission_analytics_dashboard, name='admission_analytics_dashboard'),
    path('analytics/export/', views.export_admission_results, name='export_admission_results'),
    path('analytics/export/<int:cycle_id>/', views.export_admission_results, name='export_admission_results'),
    path('analytics/export/<int:cycle_id>/online/', views.export_admission_results, {'admission_type': 'online'}, name='export_online'),
    path('analytics/export/<int:cycle_id>/offline/', views.export_admission_results, {'admission_type': 'offline'}, name='export_offline'),
    path('analytics/session/<int:pk>/delete/', views.delete_admission_session, name='delete_admission_session'),
    path('analytics/template/download/', views.download_sample_xlsx, name='download_sample_xlsx'),
    
    # Master Answers
    path('analytics/master-answers/', views.master_answer_setup, name='master_answer_setup'),
    path('analytics/master-answers/<int:cycle_id>/', views.master_answer_setup, name='master_answer_setup_cycle'),
    
    # Recalculate
    path('analytics/recalculate/', views.recalculate_results, name='recalculate_results'),
    path('analytics/recalculate/<int:cycle_id>/', views.recalculate_results, name='recalculate_results_cycle'),
    
    # Extra Analytics
    path('analytics/subject-rankings/', views.subject_top_students, name='subject_top_students'),
    path('analytics/school-subjects/', views.school_subject_analytics, name='school_subject_analytics'),
    
    # Admission Registration (public)
    path('register/', views.admission_register, name='admission_register'),
    path('registrations/', views.admission_registrations_list, name='admission_registrations_list'),
    
    # Online Admission Analytics (Dedicated Flow)
    path('online-analytics/', views.online_analytics_dashboard, name='online_analytics_dashboard'),
    path('online-analytics/subjects/', views.online_subject_analytics, name='online_subject_analytics'),
    path('online-analytics/schools/', views.online_school_analytics, name='online_school_analytics'),
    path('online-analytics/top/', views.online_top_students, name='online_top_students'),
    path('online-analytics/export/full/', views.export_online_results_full, name='export_online_results_full'),
    path('online-analytics/recalculate-all/', views.recalculate_all_online_results, name='recalculate_all_online_results'),

    # Round Results (Admin)
    path('round-results/', views.round_results_admin, name='round_results_admin'),
    path('round-results/upload/', views.round_results_upload, name='round_results_upload'),
    path('round-results/<int:pk>/edit/', views.round_results_session_edit, name='round_results_session_edit'),
    path('round-results/update-ajax/<int:pk>/', views.round_result_update_ajax, name='round_result_update_ajax'),
    path('round-results/<int:pk>/toggle/', views.round_results_toggle_publish, name='round_results_toggle_publish'),
    path('round-results/<int:pk>/delete/', views.round_results_delete, name='round_results_delete'),

    # Student Views
    path('student/', views.student_admission_view, name='student_admission'),
    path('student/results/', views.round_results_student, name='round_results_student'),
    path('student/results/search/', views.round_results_search_ajax, name='round_results_search_ajax'),
    path('student/results/<int:pk>/', views.round_result_profile, name='round_result_profile'),
    path('student/start/<int:pk>/', views.cycle_exam_start, name='cycle_exam_start'),
    path('student/attempt/<int:attempt_pk>/', views.cycle_exam_take, name='cycle_exam_take'),
    path('student/attempt/<int:attempt_pk>/submit/', views.cycle_exam_submit, name='cycle_exam_submit'),
    path('student/attempt/<int:attempt_pk>/result/', views.cycle_exam_result, name='cycle_exam_result'),
    path('student/attempt/<int:attempt_pk>/save-answer/', views.save_answer_ajax, name='save_answer_ajax'),

]
