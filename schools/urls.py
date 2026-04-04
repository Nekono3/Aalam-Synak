from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    # Schools
    path('', views.school_list_view, name='list'),
    path('create/', views.school_create_view, name='create'),
    path('<int:pk>/', views.school_detail_view, name='detail'),
    path('<int:pk>/edit/', views.school_edit_view, name='edit'),
    path('<int:pk>/delete/', views.school_delete_view, name='delete'),
    
    # Subjects
    path('subjects/', views.subject_list_view, name='subjects'),
    path('subjects/create/', views.subject_create_view, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit_view, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete_view, name='subject_delete'),
    
    # Master Students
    path('students/', views.master_student_list_view, name='master_students'),
    path('students/upload/', views.master_student_upload_view, name='master_student_upload'),
    path('<int:school_pk>/students/add/', views.master_student_add_view, name='master_student_add'),
    path('students/<int:pk>/edit/', views.master_student_edit_view, name='master_student_edit'),
    path('students/<int:pk>/delete/', views.master_student_delete_view, name='master_student_delete'),
    
    # Class Management
    path('classes/', views.class_list_view, name='class_list'),
    path('classes/create/', views.class_create_view, name='class_create'),
    path('classes/<int:pk>/', views.class_detail_view, name='class_detail'),
    path('classes/<int:pk>/add-students/', views.class_student_add_view, name='class_student_add'),
    path('classes/<int:pk>/generate-credentials/', views.generate_credentials_view, name='generate_credentials'),
    path('classes/<int:pk>/print-credentials/', views.print_credentials_view, name='print_credentials'),
    path('student/<int:pk>/reset-password/', views.reset_student_password_view, name='reset_student_password'),
    path('student/<int:pk>/delete/', views.delete_student_from_class_view, name='delete_student'),
]

