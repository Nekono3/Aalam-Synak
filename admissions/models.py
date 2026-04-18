from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class AdmissionCycle(models.Model):
    """
    Represents an admission cycle (e.g., "Admission Spring 2026").
    Each cycle is linked to an OnlineExam from the exams app.
    """
    name = models.CharField(max_length=200, verbose_name=_('Cycle Name'))
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    
    timer_minutes = models.PositiveIntegerField(
        default=60, 
        verbose_name=_('Timer (minutes)'),
        help_text=_('Duration of the online admission exam.')
    )
    
    # Proctoring – configurable per cycle
    enable_tab_warnings = models.BooleanField(
        default=True,
        verbose_name=_('Enable Tab Switch Warnings'),
        help_text=_('If disabled, students can switch tabs without warnings.')
    )
    max_tab_switches = models.PositiveIntegerField(
        default=3,
        verbose_name=_('Max Tab Switches Before Lock')
    )

    passing_score = models.PositiveIntegerField(
        default=60, 
        verbose_name=_('Passing Score (%)'),
        help_text=_('Minimum percentage required to pass for this cycle.')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Admission Cycle')
        verbose_name_plural = _('Admission Cycles')
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class CycleLink(models.Model):
    """
    Configurable links shown to students who pass the admission exam.
    E.g. WhatsApp group links, Telegram channels, etc.
    """
    GENDER_TARGET_CHOICES = [
        ('all', _('All')),
        ('M', _('Boys')),
        ('F', _('Girls')),
    ]
    
    cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name='links',
        verbose_name=_('Cycle')
    )
    title = models.CharField(max_length=200, verbose_name=_('Link Title'))
    url = models.URLField(max_length=500, verbose_name=_('URL'))
    target_gender = models.CharField(
        max_length=5, 
        choices=GENDER_TARGET_CHOICES, 
        default='all', 
        verbose_name=_('Target Gender')
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))

    class Meta:
        verbose_name = _('Cycle Link')
        verbose_name_plural = _('Cycle Links')
        ordering = ['order', 'pk']

    def __str__(self):
        return f"{self.title} ({self.cycle.name})"


class Region(models.Model):
    """Admin-configurable region for student registration forms."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Region Name'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))

    class Meta:
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def get_region_choices(cls):
        """Return choices list from DB regions + permanent Башка option."""
        choices = [('', _('-- Выберите регион --'))]
        for r in cls.objects.all():
            choices.append((r.name, r.name))
        choices.append(('Башка', _('Башка (Другой)')))
        return choices


class ExternalSchool(models.Model):
    """
    Registry for external schools that candidates are coming from.
    Includes a unique school_id for identification.
    """
    name = models.CharField(max_length=255, verbose_name=_('School Name'))
    school_id = models.CharField(max_length=50, unique=True, verbose_name=_('School ID'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('External School')
        verbose_name_plural = _('External Schools')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.school_id})"

class AdmissionCandidate(models.Model):
    """
    Extension of the User model for admission-specific data.
    Candidates are students who register themselves.
    """
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admission_profile',
        verbose_name=_('User')
    )
    
    birth_date = models.DateField(null=True, blank=True, verbose_name=_('Birth Date'))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_('Gender'))
    address = models.TextField(verbose_name=_('Address'))
    
    # Linked to ExternalSchool registry
    previous_school = models.ForeignKey(
        ExternalSchool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates',
        verbose_name=_('Previous School')
    )
    grade_applying_for = models.CharField(max_length=10, blank=True, null=True, verbose_name=_('Grade Applying For'))
    
    # Tracking cycle association
    cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates',
        verbose_name=_('Admission Cycle')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Admission Candidate')
        verbose_name_plural = _('Admission Candidates')
        ordering = ['-created_at']

    def __str__(self):
        return self.user.get_full_name()


class AdmissionUploadSession(models.Model):
    """Tracks a batch upload of offline admission results."""
    ADMISSION_TYPE_CHOICES = [
        ('online', _('Online')),
        ('offline', _('Offline')),
    ]
    
    cycle = models.ForeignKey(AdmissionCycle, on_delete=models.CASCADE, related_name='upload_sessions')
    region = models.CharField(max_length=100, verbose_name=_('Region'))
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES, verbose_name=_('Admission Type'))
    file = models.FileField(upload_to='admission_uploads/', verbose_name=_('XLSX File'))
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = _('Admission Upload Session')
        verbose_name_plural = _('Admission Upload Sessions')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.admission_type.title()} - {self.region} ({self.uploaded_at.strftime('%Y-%m-%d')})"


class AdmissionResult(models.Model):
    """Consolidated result for a candidate in an admission cycle."""
    ADMISSION_TYPE_CHOICES = [
        ('online', _('Online')),
        ('offline', _('Offline')),
    ]
    
    VARIANT_CHOICES = [
        ('1A', '1A'),
        ('1B', '1B'),
        ('2A', '2A'),
        ('2B', '2B'),
    ]
    
    cycle = models.ForeignKey(AdmissionCycle, on_delete=models.CASCADE, related_name='results')
    candidate = models.ForeignKey(AdmissionCandidate, on_delete=models.SET_NULL, null=True, blank=True, related_name='admission_results')
    
    # Basic info (duplicated for offline/quick access)
    first_name = models.CharField(max_length=255, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=255, verbose_name=_('Last Name'))
    school_name = models.CharField(max_length=255, verbose_name=_('School Name'))
    region = models.CharField(max_length=100, verbose_name=_('Region'))
    
    # Variant and raw answer data
    variant = models.CharField(max_length=5, choices=VARIANT_CHOICES, blank=True, default='', verbose_name=_('Variant'))
    answer_string = models.TextField(blank=True, default='', verbose_name=_('Raw Answer String'))
    
    score = models.FloatField(verbose_name=_('Score'))
    total_questions = models.IntegerField(default=70, verbose_name=_('Total Questions'))
    percentage = models.FloatField(verbose_name=_('Percentage'))
    
    # Correct/wrong counts (out of 70)
    correct_count = models.IntegerField(default=0, verbose_name=_('Correct Answers'))
    wrong_count = models.IntegerField(default=0, verbose_name=_('Wrong Answers'))
    
    phone1 = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Phone 1'))
    phone2 = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Phone 2'))
    
    is_passed = models.BooleanField(default=False, verbose_name=_('Is Passed'))
    
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES, verbose_name=_('Admission Type'))
    
    # Links to sources
    upload_session = models.ForeignKey(AdmissionUploadSession, on_delete=models.CASCADE, null=True, blank=True, related_name='results')
    exam_attempt = models.OneToOneField('OnlineAttempt', on_delete=models.SET_NULL, null=True, blank=True, related_name='admission_result')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Admission Result')
        verbose_name_plural = _('Admission Results')
        ordering = ['-score']

    @property
    def medal(self):
        """Returns the medal category based on percentage."""
        if self.percentage >= 75:
            return 'gold'
        elif self.percentage >= 60:
            return 'silver'
        elif self.percentage >= 50:
            return 'bronze'
        return None

    @property
    def incorrect_percentage(self):
        """Returns the percentage of incorrect answers."""
        return 100 - self.percentage if self.percentage is not None else 100

    @property
    def medal_icon(self):
        """Returns the emoji icon for the medal."""
        medals = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}
        return medals.get(self.medal, '')

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.score}"


class AdmissionMasterAnswer(models.Model):
    """Master answer key per variant for an admission cycle."""
    VARIANT_CHOICES = [
        ('1A', '1A'),
        ('1B', '1B'),
        ('2A', '2A'),
        ('2B', '2B'),
    ]
    
    cycle = models.ForeignKey(AdmissionCycle, on_delete=models.CASCADE, related_name='master_answers')
    variant = models.CharField(max_length=5, choices=VARIANT_CHOICES, verbose_name=_('Variant'))
    answers = models.TextField(verbose_name=_('Answer Key (70 characters)'),
                               help_text=_('Enter the 70-character answer key string. E.g. АБВГАБВГ...'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Master Answer')
        verbose_name_plural = _('Master Answers')
        unique_together = ['cycle', 'variant']
    
    def __str__(self):
        return f"{self.cycle.name} - Variant {self.variant}"
    
    @property
    def answer_count(self):
        return len(self.answers) if self.answers else 0


class AdmissionSubjectSplit(models.Model):
    """Defines question ranges per subject per variant."""
    VARIANT_CHOICES = [
        ('1A', '1A'),
        ('1B', '1B'),
        ('2A', '2A'),
        ('2B', '2B'),
    ]
    
    cycle = models.ForeignKey(AdmissionCycle, on_delete=models.CASCADE, related_name='subject_splits')
    variant = models.CharField(max_length=5, choices=VARIANT_CHOICES, verbose_name=_('Variant'))
    subject_name = models.CharField(max_length=100, verbose_name=_('Subject Name'))
    start_question = models.PositiveIntegerField(verbose_name=_('Start Question (1-indexed)'))
    end_question = models.PositiveIntegerField(verbose_name=_('End Question (1-indexed, inclusive)'))
    
    class Meta:
        verbose_name = _('Subject Split')
        verbose_name_plural = _('Subject Splits')
        ordering = ['variant', 'start_question']
    
    def __str__(self):
        return f"{self.variant}: {self.subject_name} (Q{self.start_question}-Q{self.end_question})"
    
    @property
    def question_count(self):
        return self.end_question - self.start_question + 1


class AdmissionSubjectScore(models.Model):
    """Per-student, per-subject score breakdown."""
    result = models.ForeignKey(AdmissionResult, on_delete=models.CASCADE, related_name='subject_scores')
    subject_name = models.CharField(max_length=100, verbose_name=_('Subject Name'))
    correct_count = models.IntegerField(default=0, verbose_name=_('Correct Answers'))
    wrong_count = models.IntegerField(default=0, verbose_name=_('Wrong Answers'))
    total_questions = models.IntegerField(default=0, verbose_name=_('Total Questions'))
    
    class Meta:
        verbose_name = _('Subject Score')
        verbose_name_plural = _('Subject Scores')
        ordering = ['subject_name']
    
    def __str__(self):
        return f"{self.result} - {self.subject_name}: {self.correct_count}/{self.total_questions}"
    
    @property
    def percentage(self):
        return (self.correct_count / self.total_questions * 100) if self.total_questions > 0 else 0


class AdmissionRegistration(models.Model):
    """Lightweight student self-registration for admission (no user account required).
    
    Students type their own school name and region freely.
    This data feeds into analytics, exports, and online exam assignment.
    """
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
    ]
    VARIANT_CHOICES = [
        ('1A', '1A'),
        ('1B', '1B'),
        ('2A', '2A'),
        ('2B', '2B'),
    ]

    cycle = models.ForeignKey(AdmissionCycle, on_delete=models.CASCADE, related_name='registrations')
    full_name = models.CharField(max_length=255, verbose_name=_('Full Name (ФИО)'))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_('Gender'))
    school_name = models.CharField(max_length=255, verbose_name=_('School Name'))
    region = models.CharField(max_length=100, verbose_name=_('Region'))
    phone1 = models.CharField(max_length=50, verbose_name=_('Phone 1'))
    phone2 = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Phone 2'))
    variant = models.CharField(max_length=5, choices=VARIANT_CHOICES, verbose_name=_('Variant'))
    
    # Link to user account if they proceed to online exam
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='admission_registrations',
        verbose_name=_('User Account')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Admission Registration')
        verbose_name_plural = _('Admission Registrations')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} — {self.school_name} ({self.region})"


# ============================================================
# ADMISSION ONLINE EXAM SYSTEM (Directly connected to Cycles)
# ============================================================

class AdmissionQuestion(models.Model):
    """Question for an admission cycle's online exam."""
    
    cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name='admission_questions',
        verbose_name=_('Admission Cycle')
    )
    
    question_text = models.TextField(verbose_name=_('Question Text'))
    question_image = models.ImageField(
        upload_to='admission_questions/',
        blank=True, null=True,
        verbose_name=_('Question Image')
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    points = models.PositiveIntegerField(default=1, verbose_name=_('Points'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Admission Question')
        verbose_name_plural = _('Admission Questions')
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class AdmissionQuestionOption(models.Model):
    """Answer option for an admission question."""
    
    question = models.ForeignKey(
        AdmissionQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('Question')
    )
    
    text = models.CharField(max_length=500, verbose_name=_('Option Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Correct Answer'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    
    class Meta:
        verbose_name = _('Admission Question Option')
        verbose_name_plural = _('Admission Question Options')
        ordering = ['order', 'id']
    
    def __str__(self):
        return self.text[:50]


class OnlineAttempt(models.Model):
    """Student's active attempt at an online admission exam.
    Once completed, its data is converted into an AdmissionResult."""
    
    STATUS_CHOICES = [
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('locked', _('Locked')),
        ('timed_out', _('Timed Out')),
    ]
    
    cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name='online_attempts',
        verbose_name=_('Admission Cycle')
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='online_admission_attempts',
        verbose_name=_('Student')
    )
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Started At'))
    
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress',
        verbose_name=_('Status')
    )
    
    # Proctoring
    tab_switch_count = models.PositiveIntegerField(default=0, verbose_name=_('Tab Switch Count'))
    lock_reason = models.CharField(max_length=200, blank=True, verbose_name=_('Lock Reason'))
    
    class Meta:
        verbose_name = _('Online Exam Attempt')
        verbose_name_plural = _('Online Exam Attempts')
        ordering = ['-started_at']
        unique_together = ['cycle', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.cycle.name}"
    
    @property
    def time_remaining(self):
        from django.utils import timezone
        if self.status != 'in_progress':
            return 0
        elapsed = (timezone.now() - self.started_at).total_seconds()
        remaining = (self.cycle.timer_minutes * 60) - elapsed
        return max(0, int(remaining))


class OnlineAttemptAnswer(models.Model):
    """Individual answer during an active online attempt."""
    
    attempt = models.ForeignKey(
        OnlineAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Attempt')
    )
    question = models.ForeignKey(
        AdmissionQuestion,
        on_delete=models.CASCADE,
        related_name='attempt_answers',
        verbose_name=_('Question')
    )
    selected_option = models.ForeignKey(
        AdmissionQuestionOption,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='selections',
        verbose_name=_('Selected Option')
    )
    
    answered_at = models.DateTimeField(auto_now=True, verbose_name=_('Answered At'))
    
    class Meta:
        verbose_name = _('Online Attempt Answer')
        verbose_name_plural = _('Online Attempt Answers')
        unique_together = ['attempt', 'question']


# ============================================================
# ROUND RESULTS — Excel-based admission results for students
# ============================================================

class RoundResultSession(models.Model):
    """An upload session for round results (e.g. '1-тур жыйынтыгы')."""
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    file = models.FileField(upload_to='round_results/', verbose_name=_('Excel File'))
    is_published = models.BooleanField(default=False, verbose_name=_('Published'))
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('Uploaded By')
    )
    passing_score = models.FloatField(default=24.0, verbose_name=_('Passing Score Threshold'))

    class Meta:
        verbose_name = _('Round Result Session')
        verbose_name_plural = _('Round Result Sessions')
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title


class RoundResult(models.Model):
    """Individual student result row imported from Excel."""
    STATUS_CHOICES = [
        ('accepted', _('Өттү')),
        ('rejected', _('Өтпөдү')),
    ]

    session = models.ForeignKey(
        RoundResultSession,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_('Session')
    )
    full_name = models.CharField(max_length=300, verbose_name=_('Full Name'))
    gender = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Gender'))
    district = models.CharField(max_length=200, blank=True, default='', verbose_name=_('District'))
    school = models.CharField(max_length=300, blank=True, default='', verbose_name=_('School'))
    phone1 = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Phone 1'))
    phone2 = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Phone 2'))

    # Subject scores (raw score like 8) and percentages
    math_score = models.FloatField(null=True, blank=True, verbose_name=_('Math Score'))
    math_pct = models.FloatField(null=True, blank=True, verbose_name=_('Math %'))
    kyrgyz_score = models.FloatField(null=True, blank=True, verbose_name=_('Kyrgyz Score'))
    kyrgyz_pct = models.FloatField(null=True, blank=True, verbose_name=_('Kyrgyz %'))
    biology_score = models.FloatField(null=True, blank=True, verbose_name=_('Biology Score'))
    biology_pct = models.FloatField(null=True, blank=True, verbose_name=_('Biology %'))
    geography_score = models.FloatField(null=True, blank=True, verbose_name=_('Geography Score'))
    geography_pct = models.FloatField(null=True, blank=True, verbose_name=_('Geography %'))
    history_score = models.FloatField(null=True, blank=True, verbose_name=_('History Score'))
    history_pct = models.FloatField(null=True, blank=True, verbose_name=_('History %'))
    english_score = models.FloatField(null=True, blank=True, verbose_name=_('English Score'))
    english_pct = models.FloatField(null=True, blank=True, verbose_name=_('English %'))
    russian_score = models.FloatField(null=True, blank=True, verbose_name=_('Russian Score'))
    russian_pct = models.FloatField(null=True, blank=True, verbose_name=_('Russian %'))

    # Totals
    total_score = models.FloatField(default=0, verbose_name=_('Total Score'))
    total_pct = models.FloatField(default=0, verbose_name=_('Total %'))

    # Medal & Status
    medal = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Medal'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rejected',
        verbose_name=_('Status')
    )

    class Meta:
        verbose_name = _('Round Result')
        verbose_name_plural = _('Round Results')
        ordering = ['-total_score']

    def __str__(self):
        return f"{self.full_name} — {self.total_score}"

