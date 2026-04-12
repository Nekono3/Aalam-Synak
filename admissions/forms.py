from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    AdmissionUploadSession, AdmissionCycle,
    AdmissionQuestion, AdmissionQuestionOption, AdmissionSubjectSplit
)

class AdmissionXLSXUploadForm(forms.Form):
    cycle = forms.ModelChoiceField(
        queryset=AdmissionCycle.objects.filter(is_active=True),
        label=_("Admission Cycle"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    REGION_CHOICES = [
        ('', _('-- Выберите регион --')),
        ('Баткен', _('Баткен')),
        ('Бишкек', _('Бишкек')),
        ('Джалал-Абад', _('Джалал-Абад')),
        ('Иссык-Куль', _('Иссык-Куль')),
        ('Нарын', _('Нарын')),
        ('Ош (город)', _('Ош (город)')),
        ('Ошская область', _('Ошская область')),
        ('Талас', _('Талас')),
        ('Чуй', _('Чуй')),
    ]
    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        label=_("Region"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    admission_type = forms.ChoiceField(
        choices=AdmissionUploadSession.ADMISSION_TYPE_CHOICES,
        label=_("Admission Type"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    file = forms.FileField(
        label=_("XLSX File"),
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.xlsx'})
    )


class AdmissionRegistrationForm(forms.Form):
    """Form for student self-registration in admission."""
    GENDER_CHOICES = [
        ('', _('-- Выберите --')),
        ('M', _('Бала (Male)')),
        ('F', _('Кыз (Female)')),
    ]
    VARIANT_CHOICES = [
        ('', _('-- Выберите --')),
        ('1A', '1A'),
        ('1B', '1B'),
        ('2A', '2A'),
        ('2B', '2B'),
    ]

    full_name = forms.CharField(
        max_length=255,
        label=_("Full Name (ФИО)"),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Напр: Иванов Иван Иванович'),
        })
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        label=_("Gender"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    school_name = forms.CharField(
        max_length=255,
        label=_("School Name"),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Напр: №15 мектеп, Бишкек'),
        })
    )
    REGION_CHOICES = [
        ('', _('-- Выберите регион --')),
        ('Баткен', _('Баткен')),
        ('Бишкек', _('Бишкек')),
        ('Джалал-Абад', _('Джалал-Абад')),
        ('Иссык-Куль', _('Иссык-Куль')),
        ('Нарын', _('Нарын')),
        ('Ош (город)', _('Ош (город)')),
        ('Ошская область', _('Ошская область')),
        ('Талас', _('Талас')),
        ('Чуй', _('Чуй')),
        ('Башка', _('Башка (Другой)')),
    ]
    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        label=_("Region"),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_region'})
    )
    custom_region = forms.CharField(
        max_length=100,
        required=False,
        label=_("Your Region"),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Напр: Казахстан, Узбекистан...'),
            'id': 'id_custom_region',
        })
    )

    def clean(self):
        cleaned = super().clean()
        region = cleaned.get('region', '')
        custom_region = cleaned.get('custom_region', '').strip()
        if region == 'Башка':
            if not custom_region:
                self.add_error('custom_region', _('Please enter your region.'))
            else:
                cleaned['region'] = custom_region
        return cleaned
    phone1 = forms.CharField(
        max_length=50,
        label='Номериңиз',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Напр: 0555 123 456'),
        })
    )
    phone2 = forms.CharField(
        max_length=50,
        required=True,
        label='Ата-энеңиздин номери',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Напр: 0555 123 456'),
        })
    )
    variant = forms.ChoiceField(
        choices=VARIANT_CHOICES,
        label=_("Exam Variant"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AdmissionQuestionForm(forms.ModelForm):
    """Form for creating/editing admission cycle questions."""
    
    class Meta:
        model = AdmissionQuestion
        fields = ['question_text', 'question_image', 'points', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


class AdmissionQuestionOptionForm(forms.ModelForm):
    """Form for creating/editing admission question options."""
    
    class Meta:
        model = AdmissionQuestionOption
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


AdmissionQuestionOptionFormSet = forms.inlineformset_factory(
    AdmissionQuestion,
    AdmissionQuestionOption,
    form=AdmissionQuestionOptionForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True
)

class AdmissionSubjectSplitForm(forms.ModelForm):
    """Form for defining subject ranges."""
    class Meta:
        model = AdmissionSubjectSplit
        fields = ['subject_name', 'start_question', 'end_question']
        widgets = {
            'subject_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('e.g. Math, Biology, English')
            }),
            'start_question': forms.NumberInput(attrs={
                'class': 'form-input', 'min': 1,
                'placeholder': _('e.g. 1')
            }),
            'end_question': forms.NumberInput(attrs={
                'class': 'form-input', 'min': 1,
                'placeholder': _('e.g. 20')
            }),
        }

AdmissionSubjectSplitFormSet = forms.inlineformset_factory(
    AdmissionCycle,
    AdmissionSubjectSplit,
    form=AdmissionSubjectSplitForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False
)

