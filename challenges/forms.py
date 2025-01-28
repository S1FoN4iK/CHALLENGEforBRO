from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Challenge, Book, Quiz, Answer, AudioChallenge

# Форма регистрации пользователя
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']

# Форма для выбора книги в челлендже
class BookSelectionForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.all(), required=True)

# Форма для прохождения квиза
class QuizAnswerForm(forms.Form):
    answers = forms.ModelMultipleChoiceField(queryset=Answer.objects.all(), required=True)

class AudioChallengeForm(forms.Form):
    user_answer = forms.CharField(max_length=255, required=True, label="Ваш ответ")

    def __init__(self, *args, **kwargs):
        self.audio_challenge = kwargs.pop('audio_challenge', None)
        super().__init__(*args, **kwargs)

    def clean_user_answer(self):
        answer = self.cleaned_data.get("user_answer").strip().lower()  # Приводим ответ к нижнему регистру

        if self.audio_challenge:
            if answer != self.audio_challenge.correct_answer.strip().lower():
                raise forms.ValidationError("Ответ неправильный. Попробуйте снова.")
        else:
            raise forms.ValidationError("Отсутствует объект audio_challenge.")

        return answer

