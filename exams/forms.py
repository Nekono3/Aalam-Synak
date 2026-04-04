from django import forms
from django.utils.translation import gettext_lazy as _
from .models import OnlineExam, ExamQuestion, QuestionOption, MatchingPair, OrderingItem


class OnlineExamForm(forms.ModelForm):
    """Form for creating/editing online exams."""
    
    class Meta:
        model = OnlineExam
        fields = [
            'title', 'description', 'subject', 'school',
            'duration_minutes', 'passing_score',
            'start_time', 'end_time',
            'shuffle_questions', 'shuffle_options',
            'show_results_immediately', 'max_tab_switches',
            'prevent_go_back', 'enable_recording', 'enable_proctoring',
            'target_classes', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 100}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'max_tab_switches': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
            'target_classes': forms.CheckboxSelectMultiple(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_('End time must be after start time.'))
        
        return cleaned_data


class ExamQuestionForm(forms.ModelForm):
    """Form for creating/editing exam questions."""
    
    class Meta:
        model = ExamQuestion
        fields = ['question_text', 'question_image', 'question_type', 'points', 'correct_answers', 'correct_answer_boolean', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_question_type'}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'correct_answers': forms.Textarea(attrs={
                'class': 'form-input', 
                'rows': 2,
                'placeholder': _('For fill-in-the-blanks: enter correct answers separated by | (pipe). Example: answer1|answer2|answer3')
            }),
            'correct_answer_boolean': forms.Select(
                choices=[('', _('--- Select ---')), (True, _('True')), (False, _('False'))],
                attrs={'class': 'form-select'}
            ),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


class QuestionOptionForm(forms.ModelForm):
    """Form for creating/editing question options."""
    
    class Meta:
        model = QuestionOption
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


class MatchingPairForm(forms.ModelForm):
    """Form for creating/editing matching pairs."""
    
    class Meta:
        model = MatchingPair
        fields = ['left_item', 'right_item', 'order']
        widgets = {
            'left_item': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Column A item')}),
            'right_item': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Column B item')}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


class OrderingItemForm(forms.ModelForm):
    """Form for creating/editing ordering items."""
    
    class Meta:
        model = OrderingItem
        fields = ['text', 'correct_position']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Item text')}),
            'correct_position': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': _('Position')}),
        }


# Formsets for inline editing
QuestionOptionFormSet = forms.inlineformset_factory(
    ExamQuestion,
    QuestionOption,
    form=QuestionOptionForm,
    extra=4,
    can_delete=True,
    min_num=0,
    validate_min=False
)

MatchingPairFormSet = forms.inlineformset_factory(
    ExamQuestion,
    MatchingPair,
    form=MatchingPairForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False
)

OrderingItemFormSet = forms.inlineformset_factory(
    ExamQuestion,
    OrderingItem,
    form=OrderingItemForm,
    extra=4,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class AnswerForm(forms.Form):
    """Form for submitting an answer during exam."""
    question_id = forms.IntegerField(widget=forms.HiddenInput())
    option_id = forms.IntegerField(required=False)
