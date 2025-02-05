from django.db import models
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

def get_default_end_time():
    """Возвращает текущее время + 5 минут."""
    return now() + timedelta(minutes=5) #Нерабочий кусок моей попытки в таймеры не со стороны пользователя

class Challenge(models.Model):
    """Модель для описания челленджа."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    image = models.ImageField(upload_to='challenge_images/', null=True, blank=True)  # Поле для изображения

    def __str__(self):
        return self.title

class CouponImage(models.Model):
    """Модель для изображения купона, привязанного к челленджу."""
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='coupon_images')
    image = models.ImageField(upload_to='coupon_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Coupon image for {self.challenge.title}"

class SupportMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_answered = models.BooleanField(default=False)

    def __str__(self):
        return f"Сообщение от {self.user.username} ({self.created_at})"

class SupportResponse(models.Model):
    message = models.ForeignKey(SupportMessage, on_delete=models.CASCADE, related_name='responses')
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    response = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Ответ от {self.admin.username} на сообщение #{self.message.id}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')

    def __str__(self):
        return self.user.username

class DailyCoupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    def generate_coupon(self):
        """Генерируем случайный код купона и скидку."""
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))  # Генерация случайного кода
        discount = random.choice([5.0, 10.0, 15.0, 20.0])  # Скидка: 5%, 10%, 15% или 20%
        self.code = code
        self.discount = discount

    def is_new_day(self):
        """Проверяем, прошло ли 24 часа с последнего обновления"""
        if not self.last_updated:
            return True
        return timezone.now() - self.last_updated >= timedelta(days=1)

    def save(self, *args, **kwargs):
        """Переопределяем метод save для генерации нового купона, если прошло 24 часа."""
        if self.is_new_day() or not self.pk:
            self.generate_coupon()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Coupon {self.code} - {self.discount}%"

class CompletedChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'challenge') 
        ordering = ['completed_at'] 

    def __str__(self):
        return f"{self.user.username} завершил {self.challenge.title}"



class ChallengeTask(models.Model):
    """Задачи, входящие в челлендж."""
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Book(models.Model):
    title = models.CharField(max_length=255)  # Название книги
    author = models.CharField(max_length=255)  # Автор
    description = models.TextField()  # Краткое описание
    image = models.ImageField(upload_to='book_covers/', null=True, blank=True)  # Обложка книги
    full_text = models.TextField(default="Текст отсутствует")
    challenge = models.ForeignKey('Challenge', on_delete=models.CASCADE)  # Привязка к челленджу

    def __str__(self):
        return self.title


class Participant(models.Model):
    """Модель участника челленджа."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='participants')
    progress = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"

class BookTimer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(default=get_default_end_time)
    is_completed = models.BooleanField(default=False)

    def check_timer(self):
        """Проверить, завершился ли таймер."""
        if now() >= self.end_time:
            self.is_completed = True
            self.save()
            return True
        return False #Тут тоже остаток, таймер понадобился лишь в 1 челлендже профитнее сделать его на js


class Quiz(models.Model):
    name = models.CharField(max_length=255, default="Default Quiz Name", verbose_name="Название")
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Дата создания") 
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name="quizzes",
        verbose_name="Челлендж",
        null=True, 
        blank=True 
    )
    image = models.ImageField(upload_to='quiz_images/', null=True, blank=True, verbose_name="Изображение") 

    def __str__(self):
        return self.name


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name="questions", on_delete=models.CASCADE, verbose_name="Квиз")
    text = models.TextField(null=True, verbose_name="Текст вопроса") 

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE, verbose_name="Вопрос")
    text = models.CharField(max_length=200, verbose_name="Ответ")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")

    def __str__(self):
        return self.text

class AudioChallenge(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    challenge = models.ForeignKey(
        'Challenge',
        null=True,
        on_delete=models.CASCADE,
        related_name="audio_challenges",
        verbose_name="Челлендж"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class AudioQuestion(models.Model):
    audio_challenge = models.ForeignKey(AudioChallenge, on_delete=models.CASCADE, related_name='questions')
    audio_file = models.FileField(upload_to='audio_questions/')
    correct_answer = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)  # Для порядка вопросов

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Вопрос {self.order} для {self.audio_challenge.title}"




