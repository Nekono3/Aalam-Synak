from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User


class LoginForm(forms.Form):
    """User login form with email or username authentication."""
    
    login = forms.CharField(
        label=_('Email же колдонуучу аты'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Email же колдонуучу атыңызды жазыңыз'),
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_('Сырсөз'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Сырсөзүңүздү жазыңыз'),
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label=_('Мени эстеп калуу'),
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        login_value = self.cleaned_data.get('login', '').strip()
        password = self.cleaned_data.get('password')
        
        if login_value and password:
            # EmailOrUsernameBackend handles both email and username lookup
            self.user_cache = authenticate(self.request, username=login_value, password=password)
            
            if self.user_cache is None:
                raise forms.ValidationError(_('Invalid email/username or password.'))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_('This account is inactive.'))
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache

class StudentRegistrationForm(forms.ModelForm):
    """Student registration form with all required fields."""
    
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Create a password'),
        })
    )
    password_confirm = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirm your password'),
        })
    )
    
    # Extra fields for AdmissionCandidate profile
    gender = forms.ChoiceField(
        label=_('Gender'),
        choices=[('', _('-- Выберите --')), ('M', _('Эркек')), ('F', _('Кыз'))],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    ADDRESS_CHOICES = [
        ('', _('-- Выберите регион --')),
        ('Сүлүктү ш.', 'Сүлүктү ш.'),
        ('Лейлек р.', 'Лейлек р.'),
        ('Баткен ш.', 'Баткен ш.'),
        ('Баткен р.', 'Баткен р.'),
        ('Кадамжай р.', 'Кадамжай р.'),
        ('Кызыл-Кыя ш.', 'Кызыл-Кыя ш.'),
        ('Башка', 'Башка'),
    ]
    address = forms.ChoiceField(
        label=_('Дарек'),
        choices=ADDRESS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_address'})
    )
    custom_address = forms.CharField(
        max_length=100,
        required=False,
        label=_('Регионуңузду жазыңыз'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Мисалы: Бишкек, Казахстан...'),
            'id': 'id_custom_address',
        })
    )
    previous_school = forms.CharField(
        label=_('Мектебиңиз'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Мисалы: №15 мектеп, Бишкек'),
        })
    )
    phone = forms.CharField(
        label='Номериңиз',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Мисалы: 0555 123 456'),
        })
    )
    father_phone = forms.CharField(
        label='Ата-энеңиздин номери',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Мисалы: 0555 123 456'),
        })
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'father_phone']
        labels = {
            'first_name': _('Аты'),
            'last_name': _('Фамилиясы'),
            'email': _('Email дареги'),
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': _('Email'),
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Аты'),
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Фамилиясы'),
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required for students
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone'].required = True
        self.fields['father_phone'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This email is already registered.'))
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_('Passwords do not match.'))
        
        # Merge custom_address into address when 'Башка' is selected
        address = cleaned_data.get('address', '')
        custom_address = cleaned_data.get('custom_address', '').strip()
        if address == 'Башка':
            if not custom_address:
                self.add_error('custom_address', _('Регионуңузду жазыңыз.'))
            else:
                cleaned_data['address'] = custom_address
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'student'
        if commit:
            user.save()
            
            # Auto-create ExternalSchool from typed school name
            from admissions.views import _auto_create_external_school
            school_name = self.cleaned_data['previous_school'].strip()
            external_school = _auto_create_external_school(school_name) if school_name else None
            
            # Create the AdmissionCandidate profile
            from admissions.models import AdmissionCandidate, AdmissionCycle
            active_cycles = AdmissionCycle.objects.filter(is_active=True)
            active_cycle = active_cycles.first()
            
            AdmissionCandidate.objects.create(
                user=user,
                gender=self.cleaned_data['gender'],
                birth_date=None,  # Removed from form
                address=self.cleaned_data['address'],
                previous_school=external_school,
                grade_applying_for="N/A",  # Removed from form
                cycle=active_cycle
            )
            
            # Also create AdmissionRegistration so the school data
            # is available for export and analytics
            from admissions.models import AdmissionRegistration
            if school_name:
                for cycle in active_cycles:
                    AdmissionRegistration.objects.create(
                        cycle=cycle,
                        full_name=f"{user.first_name} {user.last_name}",
                        gender=self.cleaned_data['gender'],
                        school_name=school_name,
                        region=self.cleaned_data.get('address', ''),
                        phone1=user.phone or '',
                        phone2=user.father_phone or '',
                        variant='',
                        user=user,
                    )
        return user


class TeacherForm(forms.ModelForm):
    """Teacher creation/edit form for admins."""
    
    password = forms.CharField(
        label=_('Password'),
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Leave empty to keep current'),
        }),
        help_text=_('Leave empty to keep current password (when editing).')
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'primary_school', 'preferred_language', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'primary_school': forms.Select(attrs={'class': 'form-select'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        # Import here to avoid circular import
        from schools.models import School
        self.fields['primary_school'].queryset = School.objects.filter(is_active=True)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_('This email is already in use.'))
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        user.role = 'teacher'
        if commit:
            user.save()
        return user


class AdminForm(forms.ModelForm):
    """Admin creation/edit form (for super admins only)."""
    
    password = forms.CharField(
        label=_('Password'),
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Leave empty to keep current'),
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'preferred_language', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        user.role = 'super_admin'
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """User profile edit form."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
        }


class StudentProfileForm(forms.ModelForm):
    """Student-specific profile form with parent contact fields."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'mother_phone', 'father_phone', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'mother_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'father_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
        }


class PasswordChangeForm(BasePasswordChangeForm):
    """Custom password change form with styled fields."""
    
    old_password = forms.CharField(
        label=_('Current Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter current password'),
        })
    )
    new_password1 = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter new password'),
        })
    )
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirm new password'),
        })
    )


class AdminPasswordResetForm(forms.Form):
    """Form for admins to reset user passwords."""
    
    new_password = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter new password'),
        })
    )
    confirm_password = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirm new password'),
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        
        if password and confirm and password != confirm:
            raise forms.ValidationError(_('Passwords do not match.'))
        
        return cleaned_data
