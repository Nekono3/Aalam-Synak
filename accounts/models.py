from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for Aalam Synak platform.
    Uses email as the primary login field.
    """
    
    ROLE_CHOICES = [
        ('super_admin', _('Super Admin')),
        ('teacher', _('Teacher')),
        ('student', _('Student')),
    ]
    
    STUDENT_TYPE_CHOICES = [
        ('internal', _('Student Aalam')),
        ('applicant', _('Admission Student')),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ru', 'Русский'),
        ('ky', 'Кыргызча'),
    ]
    
    # Override username to be optional (we use email)
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)
    
    # Role-based access
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='student',
        verbose_name=_('Role')
    )
    
    # Student type differentiation
    student_type = models.CharField(
        max_length=20,
        choices=STUDENT_TYPE_CHOICES,
        default='internal',
        verbose_name=_('Student Type'),
        help_text=_('Internal = class-managed school student, Applicant = admission registrant')
    )
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'))
    mother_phone = models.CharField(max_length=20, blank=True, verbose_name=_("Mother's Phone"))
    father_phone = models.CharField(max_length=20, blank=True, verbose_name=_("Father's Phone"))
    
    # School association
    primary_school = models.ForeignKey(
        'schools.School',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('Primary School')
    )
    
    # Class assignment (for students)
    school_class = models.ForeignKey(
        'schools.SchoolClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name=_('Class')
    )
    
    # Temporary plain password storage for credential printing
    plain_password = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_('Generated Password')
    )
    
    # Preferences
    preferred_language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        verbose_name=_('Preferred Language')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.get_full_name() or self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_student(self):
        return self.role == 'student'
