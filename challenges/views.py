from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .models import Challenge, Book, Participant, Quiz, Question, Answer, CompletedChallenge, DailyCoupon
from .forms import CustomUserCreationForm, BookSelectionForm, QuizAnswerForm
from django.db.models import Count
from django.contrib.auth.models import User
from .models import AudioChallenge
from .forms import AudioChallengeForm
import random
import string
from django.utils import timezone


# Регистрация пользователя
def register(request):
    """Страница регистрации пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Аккаунт успешно создан! Теперь вы можете войти.')
            return redirect('login')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# Успешный выход
def logout_success(request):
    """Страница успешного выхода"""
    return render(request, 'logout_success.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('password_change_done')
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'change_password.html', {'form': form})

def password_change_done(request):
    return render(request, 'password_change_done.html')      

# Личный кабинет
@login_required
def profile(request):
    """Личный кабинет пользователя"""
    return render(request, 'users/profile.html', {'user': request.user})

# Список челленджей
@login_required
def challenge_list(request):
    """Список всех челленджей"""
    challenges = Challenge.objects.all()
    return render(request, 'challenges/list.html', {'challenges': challenges})

def leaderboard(request):
    leaderboard = CompletedChallenge.objects.values('user') \
        .annotate(challenge_count=Count('challenge')) \
        .order_by('-challenge_count')[:10] 
    
    leaderboard_data = []
    for entry in leaderboard:
        user = entry['user']
        user_name = User.objects.get(id=user).username 
        leaderboard_data.append({'user': user_name, 'challenge_count': entry['challenge_count']})

    return render(request, 'leaderboard.html', {'leaderboard': leaderboard_data})

# Детали челленджа
@login_required
def challenge_detail(request, challenge_id):
    """Детали конкретного челленджа"""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    tasks = challenge.tasks.all()
    return render(request, 'challenges/detail.html', {'challenge': challenge, 'tasks': tasks})

# Присоединение к челленджу
@login_required
def join_challenge(request, challenge_id):
    """Присоединение пользователя к челленджу"""
    challenge = get_object_or_404(Challenge, id=challenge_id)

    participant, created = Participant.objects.get_or_create(user=request.user, challenge=challenge)

    # Проверка, если это аудиочеллендж
    if AudioChallenge.objects.filter(challenge=challenge).exists():
        # Если это аудиочеллендж, редиректим на его страницу
        redirect_url = 'audio_challenge_list'
    elif challenge.quizzes.exists():
        # Если есть квизы, редиректим на список квизов
        redirect_url = 'quiz_list'  
    else:
        # В остальных случаях выбор книги
        redirect_url = 'book_selection'

    if created:
        messages.success(request, f'Вы успешно присоединились к челленджу: {challenge.title}')
    else:
        messages.info(request, f'Вы уже участвуете в челлендже: {challenge.title}')

    return redirect(redirect_url, challenge_id=challenge.id)

@login_required
def get_daily_coupon(request):
    coupon, created = DailyCoupon.objects.get_or_create(id=1)

    if created or coupon.last_updated is None:
        coupon.last_updated = timezone.now()
        coupon.save()

    # Если прошло больше 24 часов, обновляем купон
    if coupon.is_new_day():
        coupon.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        # Генерация случайной скидки (например, 5%, 10%, 15% или 20%)
        coupon.discount = random.choice([5.0, 10.0, 15.0, 20.0])

        # Обновляем время последнего обновления
        coupon.last_updated = timezone.now()
        coupon.save()

    time_since_last_update = timezone.now() - coupon.last_updated
    time_until_next_update_seconds = 24 * 3600 - time_since_last_update.total_seconds()

    if time_until_next_update_seconds < 3600:
        time_until_next_update = int(time_until_next_update_seconds // 60) 
        time_label = f"Осталось {time_until_next_update} минут"
    else:
        time_until_next_update = int(time_until_next_update_seconds // 3600) 
        time_label = f"Осталось {time_until_next_update} часов"

    return render(request, 'coupon_page.html', {'coupon': coupon, 'time_label': time_label})


# Выбор книг для челленджа
@login_required
def book_selection(request, challenge_id):
    """Выбор книги, связанной с челленджем"""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    books = Book.objects.filter(challenge=challenge)

    # Обработка нескольких форм на одной странице
    form_book = BookSelectionForm(request.POST or None)
    form_quiz = QuizAnswerForm(request.POST or None)

    if request.method == 'POST':
        if 'submit_book' in request.POST and form_book.is_valid():
            book = form_book.cleaned_data['book']
            return redirect('book_detail', book_id=book.id)

        elif 'submit_quiz' in request.POST and form_quiz.is_valid():
            user_answers = form_quiz.cleaned_data['answers']
            correct_answers = Answer.objects.filter(question__quiz=quiz, is_correct=True)
            correct_ids = [str(answer.id) for answer in correct_answers]
            success = set(user_answers) == set(correct_ids)

            return render(request, "quiz/quiz_complete.html", {"quiz": quiz, "success": success})

    return render(request, 'challenges/book_selection.html', {
        'challenge': challenge,
        'books': books,
        'form_book': form_book,
        'form_quiz': form_quiz,
    })

# Детали книги
def book_detail(request, book_id):
    """Отображение полной информации о книге, включая текст"""
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'challenges/book_detail.html', {'book': book})

# Список квизов
@login_required
def quiz_list(request, challenge_id):
    """Список квизов для конкретного челленджа"""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    quizzes = Quiz.objects.filter(challenge=challenge)
    return render(request, 'quiz/quiz_list.html', {'quizzes': quizzes, 'challenge': challenge})

# Вопросы квиза
@login_required
def quiz_view(request, quiz_id):
    """Прохождение квиза"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    form = QuizAnswerForm(request.POST or None)
    success = None

    if request.method == "POST" and form.is_valid():
        user_answers = form.cleaned_data['answers']
        user_answer_ids = [str(answer.id) for answer in user_answers]

        correct_answers = Answer.objects.filter(question__quiz=quiz, is_correct=True)
        correct_ids = [str(answer.id) for answer in correct_answers]

        success = set(user_answer_ids) == set(correct_ids)

        return render(request, "quiz/quiz_complete.html", {"quiz": quiz, "success": success})

    return render(request, "quiz/quiz.html", {"quiz": quiz, 'form': form, "success": success})

# Универсальная обработка ошибок
def handle_404(request, exception):
    """Обработка 404 ошибки"""
    return render(request, 'errors/404.html', status=404)

def handle_500(request):
    """Обработка 500 ошибки"""
    return render(request, 'errors/500.html', status=500)

@login_required
def audio_challenge_list(request, challenge_id):
    """Список всех аудиочелленджей для конкретного челленджа"""
    challenge = get_object_or_404(Challenge, id=challenge_id) 
    challenges = AudioChallenge.objects.filter(challenge=challenge) 
    return render(request, 'audio_challenge/audio_challenge_list.html', {'challenges': challenges, 'challenge': challenge})


@login_required
def audio_challenge_detail(request, audiochallenge_id):
    """Детали аудиочелленджа с проверкой ответа"""
    challenge = get_object_or_404(AudioChallenge, id=audiochallenge_id)
    form = AudioChallengeForm(request.POST or None, audio_challenge=challenge) 

    success = None

    if request.method == "POST" and form.is_valid():
        user_answer = form.cleaned_data['user_answer'].strip().lower()  # Приводим ответ к нижнему регистру
        correct_answer = challenge.correct_answer.strip().lower()  # Приводим правильный ответ к нижнему регистру

        # Логирование для отладки, эта часть пока не работает, но до офф защиты починится
        print(f"User answer: '{user_answer}' -> {', '.join(map(str, list(user_answer)))}")
        print(f"Correct answer: '{correct_answer}' -> {', '.join(map(str, list(correct_answer)))}")


        if user_answer == correct_answer:
            success = True
            messages.success(request, 'Поздравляем! Ответ правильный. Вы получили купон!')
            return redirect('audio_challenge_success', audiochallenge_id=challenge.id)
        else:
            success = False
            messages.error(request, 'Ответ неправильный. Попробуйте снова.')

    return render(request, 'audio_challenge/audio_challenge_detail.html', {
        'challenge': challenge, 'form': form, 'success': success
    })


def audio_challenge_success(request, audiochallenge_id):
    challenge = get_object_or_404(AudioChallenge, id=audiochallenge_id)
    return render(request, 'audio_challenge/audio_challenge_success.html', {'challenge': challenge})    


