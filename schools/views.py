from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse

from accounts.decorators import super_admin_required, teacher_or_admin_required
from .models import School, Subject, MasterStudent, SchoolClass
from .forms import SchoolForm, SubjectForm, MasterStudentUploadForm, MasterStudentForm
from .utils import parse_master_student_excel


# ============ School Views ============

@login_required
@super_admin_required
def school_list_view(request):
    """List all schools."""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    schools = School.objects.annotate(
        student_count=Count('master_students'),
        teacher_count=Count('users', filter=Q(users__role='teacher'))
    ).order_by('name')
    
    if search:
        schools = schools.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )
    
    if status == 'active':
        schools = schools.filter(is_active=True)
    elif status == 'inactive':
        schools = schools.filter(is_active=False)
    
    paginator = Paginator(schools, 20)
    page = request.GET.get('page', 1)
    schools = paginator.get_page(page)
    
    return render(request, 'schools/school_list.html', {
        'schools': schools,
        'search': search,
        'status': status,
    })


@login_required
@super_admin_required
def school_create_view(request):
    """Create a new school."""
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()
            messages.success(request, _('School "%(name)s" created successfully.') % {'name': school.name})
            return redirect('schools:list')
    else:
        form = SchoolForm()
    
    return render(request, 'schools/school_form.html', {
        'form': form,
        'title': _('Add School'),
        'submit_text': _('Create School'),
    })


@login_required
@super_admin_required
def school_edit_view(request, pk):
    """Edit an existing school."""
    school = get_object_or_404(School, pk=pk)
    
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, _('School updated successfully.'))
            return redirect('schools:list')
    else:
        form = SchoolForm(instance=school)
    
    return render(request, 'schools/school_form.html', {
        'form': form,
        'title': _('Edit School'),
        'submit_text': _('Save Changes'),
        'school': school,
    })


@login_required
@super_admin_required
def school_delete_view(request, pk):
    """Delete a school (soft delete)."""
    school = get_object_or_404(School, pk=pk)
    
    if request.method == 'POST':
        school.is_active = False
        school.save()
        messages.success(request, _('School "%(name)s" has been deactivated.') % {'name': school.name})
        return redirect('schools:list')
    
    return render(request, 'schools/school_confirm_delete.html', {'school': school})


@login_required
@super_admin_required
def school_detail_view(request, pk):
    """View school details with students."""
    school = get_object_or_404(School, pk=pk)
    
    # Get students with filtering
    search = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    
    students = school.master_students.all().order_by('grade', 'section', 'surname', 'name')
    
    if search:
        students = students.filter(
            Q(student_id__icontains=search) |
            Q(name__icontains=search) |
            Q(surname__icontains=search)
        )
    
    if grade_filter:
        students = students.filter(grade=grade_filter)
    
    # Get unique grades for filter dropdown
    grades = school.master_students.values_list('grade', flat=True).distinct().order_by('grade')
    
    paginator = Paginator(students, 50)
    page = request.GET.get('page', 1)
    students = paginator.get_page(page)
    
    return render(request, 'schools/school_detail.html', {
        'school': school,
        'students': students,
        'search': search,
        'grade_filter': grade_filter,
        'grades': grades,
    })


# ============ Subject Views ============

@login_required
@super_admin_required
def subject_list_view(request):
    """List all subjects."""
    search = request.GET.get('search', '')
    school_filter = request.GET.get('school', '')
    
    subjects = Subject.objects.filter(is_active=True).select_related('school').order_by('name')
    
    if search:
        subjects = subjects.filter(name__icontains=search)
    
    if school_filter:
        subjects = subjects.filter(school_id=school_filter)
    
    schools = School.objects.filter(is_active=True)
    
    paginator = Paginator(subjects, 20)
    page = request.GET.get('page', 1)
    subjects = paginator.get_page(page)
    
    # Convert school_filter to int for template comparison
    school_filter_int = int(school_filter) if school_filter else None
    
    return render(request, 'schools/subject_list.html', {
        'subjects': subjects,
        'search': search,
        'school_filter': school_filter,
        'school_filter_int': school_filter_int,
        'schools': schools,
    })


@login_required
@super_admin_required
def subject_create_view(request):
    """Create a new subject."""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, _('Subject "%(name)s" created successfully.') % {'name': subject.name})
            return redirect('schools:subjects')
    else:
        form = SubjectForm()
    
    return render(request, 'schools/subject_form.html', {
        'form': form,
        'title': _('Add Subject'),
        'submit_text': _('Create Subject'),
    })


@login_required
@super_admin_required
def subject_edit_view(request, pk):
    """Edit an existing subject."""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, _('Subject updated successfully.'))
            return redirect('schools:subjects')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'schools/subject_form.html', {
        'form': form,
        'title': _('Edit Subject'),
        'submit_text': _('Save Changes'),
        'subject': subject,
    })


@login_required
@super_admin_required
def subject_delete_view(request, pk):
    """Delete a subject (soft delete)."""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        subject.is_active = False
        subject.save()
        messages.success(request, _('Subject "%(name)s" has been deleted.') % {'name': subject.name})
        return redirect('schools:subjects')
    
    return render(request, 'schools/subject_confirm_delete.html', {'subject': subject})


# ============ Master Student Views ============

@login_required
@super_admin_required
def master_student_list_view(request):
    """List all master students."""
    students = MasterStudent.objects.all().select_related('school')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        from django.db.models import Q
        students = students.filter(
            Q(name__icontains=search) |
            Q(surname__icontains=search) |
            Q(student_id__icontains=search)
        )
    
    # Filter by school
    school_filter = request.GET.get('school', '')
    if school_filter:
        students = students.filter(school_id=school_filter)
    
    # Filter by grade
    grade_filter = request.GET.get('grade', '')
    if grade_filter:
        students = students.filter(grade=grade_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(students, 50)
    page = request.GET.get('page', 1)
    students = paginator.get_page(page)
    
    # Get unique grades for filter
    grades = MasterStudent.objects.values_list('grade', flat=True).distinct().order_by('grade')
    
    context = {
        'students': students,
        'search': search,
        'school_filter': int(school_filter) if school_filter else '',
        'grade_filter': grade_filter,
        'schools': School.objects.filter(is_active=True),
        'grades': grades,
    }
    
    return render(request, 'schools/master_student_list.html', context)


@login_required
@super_admin_required
def master_student_upload_view(request):
    """Upload Master Student List from Excel file."""
    if request.method == 'POST':
        form = MasterStudentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.cleaned_data['school']
            file = form.cleaned_data['file']
            replace_existing = form.cleaned_data['replace_existing']
            
            try:
                # Parse Excel file
                students_data = parse_master_student_excel(file)
                
                if not students_data:
                    messages.error(request, _('No valid student data found in the file.'))
                    return redirect('schools:master_student_upload')
                
                # Delete existing if requested
                if replace_existing:
                    MasterStudent.objects.filter(school=school).delete()
                
                # Create students
                created_count = 0
                updated_count = 0
                
                for data in students_data:
                    obj, created = MasterStudent.objects.update_or_create(
                        school=school,
                        student_id=data['student_id'],
                        defaults={
                            'name': data['name'],
                            'surname': data['surname'],
                            'grade': data['grade'],
                            'section': data['section'],
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                messages.success(
                    request,
                    _('Import complete: %(created)d students created, %(updated)d updated.') % {
                        'created': created_count,
                        'updated': updated_count,
                    }
                )
                return redirect('schools:detail', pk=school.pk)
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, _('Error processing file: %(error)s') % {'error': str(e)})
    else:
        form = MasterStudentUploadForm()
    
    return render(request, 'schools/master_student_upload.html', {
        'form': form,
    })


@login_required
@super_admin_required
def master_student_add_view(request, school_pk):
    """Manually add a student to a school."""
    school = get_object_or_404(School, pk=school_pk)
    
    if request.method == 'POST':
        form = MasterStudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = school
            student.save()
            messages.success(request, _('Student added successfully.'))
            return redirect('schools:detail', pk=school.pk)
    else:
        form = MasterStudentForm()
    
    return render(request, 'schools/master_student_form.html', {
        'form': form,
        'school': school,
        'title': _('Add Student'),
        'submit_text': _('Add Student'),
    })


@login_required
@super_admin_required
def master_student_edit_view(request, pk):
    """Edit a student."""
    student = get_object_or_404(MasterStudent, pk=pk)
    
    if request.method == 'POST':
        form = MasterStudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, _('Student updated successfully.'))
            return redirect('schools:detail', pk=student.school.pk)
    else:
        form = MasterStudentForm(instance=student)
    
    return render(request, 'schools/master_student_form.html', {
        'form': form,
        'school': student.school,
        'student': student,
        'title': _('Edit Student'),
        'submit_text': _('Save Changes'),
    })


@login_required
@super_admin_required
def master_student_delete_view(request, pk):
    """Delete a student."""
    student = get_object_or_404(MasterStudent, pk=pk)
    school_pk = student.school.pk
    
    if request.method == 'POST':
        student.delete()
        messages.success(request, _('Student deleted.'))
        return redirect('schools:detail', pk=school_pk)
    
    return render(request, 'schools/master_student_confirm_delete.html', {
        'student': student,
    })


# ============ Class Management Views ============

@login_required
@super_admin_required
def class_list_view(request):
    """List all classes with school filter."""
    school_filter = request.GET.get('school', '')
    
    classes = SchoolClass.objects.select_related('school').all()
    
    if school_filter:
        classes = classes.filter(school_id=school_filter)
    
    schools = School.objects.filter(is_active=True)
    
    # Group classes by school
    classes_by_school = {}
    for cls in classes:
        school_name = cls.school.name
        if school_name not in classes_by_school:
            classes_by_school[school_name] = []
        classes_by_school[school_name].append(cls)
    
    return render(request, 'schools/class_list.html', {
        'classes': classes,
        'classes_by_school': classes_by_school,
        'schools': schools,
        'school_filter': int(school_filter) if school_filter else '',
    })


@login_required
@super_admin_required
def class_create_view(request):
    """Create a new class."""
    if request.method == 'POST':
        school_id = request.POST.get('school')
        grade = request.POST.get('grade')
        section = request.POST.get('section')
        
        if school_id and grade and section:
            school = get_object_or_404(School, pk=school_id)
            
            # Check for duplicate
            if SchoolClass.objects.filter(school=school, grade=grade, section=section).exists():
                messages.error(request, _('Class %(grade)s%(section)s already exists for this school.') % {
                    'grade': grade, 'section': section
                })
            else:
                SchoolClass.objects.create(school=school, grade=grade, section=section)
                messages.success(request, _('Class %(grade)s%(section)s created successfully.') % {
                    'grade': grade, 'section': section
                })
                return redirect('schools:class_list')
        else:
            messages.error(request, _('Please fill in all fields.'))
    
    schools = School.objects.filter(is_active=True)
    grades = SchoolClass.GRADE_CHOICES
    sections = SchoolClass.SECTION_CHOICES
    
    return render(request, 'schools/class_form.html', {
        'schools': schools,
        'grades': grades,
        'sections': sections,
        'title': _('Add Class'),
    })


@login_required
@super_admin_required
def class_detail_view(request, pk):
    """View students in a class."""
    school_class = get_object_or_404(SchoolClass, pk=pk)
    
    from accounts.models import User
    # Get student users assigned to this class
    students = User.objects.filter(
        school_class=school_class,
        role='student'
    ).order_by('last_name', 'first_name')
    
    # Get available MasterStudent records that match this class grade/section
    available_master_students = MasterStudent.objects.filter(
        school=school_class.school,
        grade=school_class.grade,
        section=school_class.section
    ).order_by('surname', 'name')
    
    return render(request, 'schools/class_detail.html', {
        'school_class': school_class,
        'students': students,
        'available_master_students': available_master_students,
    })


@login_required
@super_admin_required
def class_student_add_view(request, pk):
    """Add students to a class from MasterStudent data."""
    school_class = get_object_or_404(SchoolClass, pk=pk)
    
    if request.method == 'POST':
        from accounts.models import User
        
        selected_ids = request.POST.getlist('master_student_ids')
        manual_name = request.POST.get('manual_name', '').strip()
        manual_surname = request.POST.get('manual_surname', '').strip()
        
        created_count = 0
        
        # Add from MasterStudent selection
        for ms_id in selected_ids:
            try:
                ms = MasterStudent.objects.get(pk=ms_id)
                # Check if student already exists
                existing = User.objects.filter(
                    first_name=ms.name,
                    last_name=ms.surname,
                    school_class=school_class,
                    role='student'
                ).exists()
                
                if not existing:
                    User.objects.create(
                        first_name=ms.name,
                        last_name=ms.surname,
                        email=f"{ms.name.lower()}.{ms.surname.lower()}.{ms.student_id}@student.aims",
                        role='student',
                        school_class=school_class,
                        primary_school=school_class.school,
                        username=None,
                    )
                    created_count += 1
            except MasterStudent.DoesNotExist:
                continue
        
        # Add manual student
        if manual_name and manual_surname:
            import random
            import string
            random_suffix = ''.join(random.choices(string.digits, k=4))
            User.objects.create(
                first_name=manual_name,
                last_name=manual_surname,
                email=f"{manual_name.lower()}.{manual_surname.lower()}.{random_suffix}@student.aims",
                role='student',
                school_class=school_class,
                primary_school=school_class.school,
                username=None,
            )
            created_count += 1
        
        if created_count:
            messages.success(request, _('%(count)d students added to class.') % {'count': created_count})
        else:
            messages.info(request, _('No new students were added.'))
        
        return redirect('schools:class_detail', pk=school_class.pk)
    
    # GET - show form with available MasterStudents
    available_master_students = MasterStudent.objects.filter(
        school=school_class.school,
        grade=school_class.grade,
        section=school_class.section
    ).order_by('surname', 'name')
    
    return render(request, 'schools/class_add_students.html', {
        'school_class': school_class,
        'available_master_students': available_master_students,
    })


@login_required
@super_admin_required
def generate_credentials_view(request, pk):
    """Auto-generate username and password for students in a class."""
    school_class = get_object_or_404(SchoolClass, pk=pk)
    
    if request.method == 'POST':
        from accounts.models import User
        import random
        import string
        
        students = User.objects.filter(
            school_class=school_class,
            role='student'
        )
        
        generated_count = 0
        grade_lower = school_class.grade.lower()
        section_lower = school_class.section.lower()
        
        for student in students:
            # Generate username: user{grade}{section}_{random5} e.g. user7a_38291
            while True:
                random_suffix = ''.join(random.choices(string.digits, k=5))
                username = f"user{grade_lower}{section_lower}_{random_suffix}"
                if not User.objects.filter(username=username).exclude(pk=student.pk).exists():
                    break
            
            # Generate password: random 8 characters 
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            student.username = username
            student.set_password(password)
            student.plain_password = password
            student.save()
            generated_count += 1
        
        messages.success(request, _('Credentials generated for %(count)d students.') % {'count': generated_count})
        return redirect('schools:class_detail', pk=school_class.pk)
    
    return redirect('schools:class_detail', pk=school_class.pk)


@login_required
@super_admin_required
def print_credentials_view(request, pk):
    """Printable page with student credentials."""
    school_class = get_object_or_404(SchoolClass, pk=pk)
    
    from accounts.models import User
    students = User.objects.filter(
        school_class=school_class,
        role='student'
    ).order_by('last_name', 'first_name')
    
    return render(request, 'schools/credentials_print.html', {
        'school_class': school_class,
        'students': students,
    })


@login_required
@super_admin_required
def reset_student_password_view(request, pk):
    """Reset a student's password and store it as plain text for admin visibility."""
    from accounts.models import User
    import random
    import string
    
    student = get_object_or_404(User, pk=pk, role='student')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        
        if not new_password:
            # Auto-generate if not provided
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        student.set_password(new_password)
        student.plain_password = new_password
        student.save()
        
        messages.success(request, _('Password reset for %(name)s. New password: %(pwd)s') % {
            'name': student.get_full_name(),
            'pwd': new_password
        })
        
        if student.school_class:
            return redirect('schools:class_detail', pk=student.school_class.pk)
        return redirect('accounts:users')
    
    return render(request, 'schools/reset_password.html', {
        'student': student,
    })


@login_required
@super_admin_required
def delete_student_from_class_view(request, pk):
    """Remove a student from the system."""
    from accounts.models import User
    
    student = get_object_or_404(User, pk=pk, role='student')
    class_pk = student.school_class.pk if student.school_class else None
    
    if request.method == 'POST':
        student_name = student.get_full_name()
        student.delete()
        messages.success(request, _('Student %(name)s removed.') % {'name': student_name})
        
        if class_pk:
            return redirect('schools:class_detail', pk=class_pk)
        return redirect('accounts:users')
    
    return redirect('schools:class_detail', pk=class_pk) if class_pk else redirect('accounts:users')
