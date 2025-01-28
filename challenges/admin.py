from django.contrib import admin
from .models import ChallengeTask, Participant, Challenge, Book, Quiz, Question, Answer, AudioChallenge

# Инлайны для вложенной работы с зависимыми объектами
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


# Кастомизация админки для моделей
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    search_fields = ['name']  # Поиск по названию квиза
    list_display = ['name', 'created_at', 'challenge']  # Отображение ключевых данных
    list_filter = ['created_at', 'challenge']  # Фильтр по дате создания и челленджу


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    search_fields = ['text']  # Поиск по тексту вопроса
    list_display = ['text', 'quiz']  # Отображение текста вопроса и квиза
    list_filter = ['quiz']  # Фильтр по квизу


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")  # Отображение текста ответа, вопроса и правильности
    search_fields = ["text"]  # Поиск по тексту ответа
    list_filter = ["is_correct"]  # Фильтр по правильности ответа


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    search_fields = ['title']  # Поиск по названию челленджа
    list_display = ['title', 'creator', 'start_date', 'end_date']  # Основные поля в списке
    list_filter = ['start_date', 'end_date']  # Фильтр по дате начала и окончания


@admin.register(ChallengeTask)
class ChallengeTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'challenge', 'is_completed']  # Основные поля в списке
    list_filter = ['is_completed']  # Фильтр по статусу выполнения
    search_fields = ['title']  # Поиск по названию задачи


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'progress']  # Отображение пользователя, челленджа и прогресса
    list_filter = ['challenge']  # Фильтр по челленджу
    search_fields = ['user__username']  # Поиск по имени пользователя


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'challenge']  # Основные поля в списке
    search_fields = ['title', 'author']  # Поиск по названию книги и автору
    list_filter = ['challenge']  # Фильтр по челленджу

@admin.register(AudioChallenge)
class AudioChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge', 'description', 'created_at')
    list_filter = ('challenge',)
    search_fields = ('title', 'challenge__title')

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'audio_file', 'correct_answer', 'challenge')
        }),
    )


