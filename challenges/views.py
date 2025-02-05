from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .models import Challenge, Book, Participant, Quiz, Question, Answer, CompletedChallenge, DailyCoupon
from .forms import CustomUserCreationForm, BookSelectionForm, QuizAnswerForm
from django.db.models import Count
from django.contrib.auth.models import User
from .models import AudioChallenge, Profile, AudioQuestion, SupportMessage
from .forms import AudioChallengeForm, ProfileForm, SupportMessageForm
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
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    if not hasattr(request.user, 'profile'):
        from .models import Profile 
        Profile.objects.create(user=request.user)  # Создаем профиль, если его нет

    return render(request, 'profile.html', {'form': form})

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
    book = get_object_or_404(Book, id=book_id)
    coupon_images = book.challenge.coupon_images.all()  
    return render(request, 'challenges/book_detail.html', {
        'book': book,
        'coupon_images': coupon_images  
    })


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
    coupon_images = quiz.challenge.coupon_images.all()
    form = QuizAnswerForm(request.POST or None)
    success = None

    if request.method == "POST" and form.is_valid():
        user_answers = form.cleaned_data['answers']
        user_answer_ids = [str(answer.id) for answer in user_answers]

        correct_answers = Answer.objects.filter(question__quiz=quiz, is_correct=True)
        correct_ids = [str(answer.id) for answer in correct_answers]

        success = set(user_answer_ids) == set(correct_ids)

        return render(request, "quiz/quiz_complete.html", {"quiz": quiz, "success": success})

    return render(request, "quiz/quiz.html", {"quiz": quiz, 'form': form, "success": success, "coupon_images": coupon_images})

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
    challenge = get_object_or_404(AudioChallenge, id=audiochallenge_id)
    questions = challenge.questions.all()

    if request.method == 'POST':
        form = AudioChallengeForm(request.POST, questions=questions)
        correct = 0
        total = questions.count()

        if form.is_valid():
            for question in questions:
                user_answer = form.cleaned_data.get(f'answer_{question.id}', '').strip().lower()
                if user_answer == question.correct_answer.lower():
                    correct += 1

            request.session['audio_success'] = {'correct': correct, 'total': total}
            return redirect('audio_challenge_success', audiochallenge_id=challenge.id)
    else:
        form = AudioChallengeForm(questions=questions)

    return render(request, 'audio_challenge/audio_challenge_detail.html', {
        'challenge': challenge,
        'form': form,
        'questions': questions
    })

@login_required
def audio_challenge_success(request, audiochallenge_id):
    results = request.session.get('audio_success', {'correct': 0, 'total': 0})
    return render(request, 'audio_challenge/audio_challenge_success.html', {
        'correct': results['correct'],
        'total': results['total']
    })

@login_required
def support_chat(request):
    form = SupportMessageForm() 
    if request.method == 'POST':
        form = SupportMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.user = request.user
            message.save()
            form = SupportMessageForm() 

    return render(request, 'support/chat_modal.html', {'form': form})
