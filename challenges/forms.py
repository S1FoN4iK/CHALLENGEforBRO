from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Challenge, Book, Quiz, Answer, AudioChallenge, Profile, SupportMessage

# Форма регистрации пользователя
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']

class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите ваше сообщение...'
            }),
        }

# Форма для выбора книги в челлендже
class BookSelectionForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.all(), required=True)

# Форма для прохождения квиза
class QuizAnswerForm(forms.Form):
    answers = forms.ModelMultipleChoiceField(queryset=Answer.objects.all(), required=True)


class AudioChallengeForm(forms.Form):
    # Динамически создаем поля для ответов
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)

        if questions:
            for question in questions:
                self.fields[f'answer_{question.id}'] = forms.CharField(
                    label=f'Ответ на вопрос {question.id}',
                    widget=forms.TextInput(attrs={'placeholder': 'Введите ваш ответ'}),
                    required=True
                )
