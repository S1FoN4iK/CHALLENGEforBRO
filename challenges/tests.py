from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Challenge, Book, CompletedChallenge, Participant

class ChallengeViewsTest(TestCase):
    def setUp(self):
        # Создание тестового пользователя
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Создание тестового челленджа
        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            description='Test Description',
            creator=self.user,
            start_date='2025-01-01',
            end_date='2025-02-01'
        )

        # Создание книги для челленджа
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            description='Test Book Description',
            challenge=self.challenge
        )

        # Логинимся
        self.client.login(username='testuser', password='testpassword')

    def test_challenge_list_view(self):
        # Тест представления для списка челленджей
        response = self.client.get(reverse('challenge_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Challenge')
        self.assertTemplateUsed(response, 'challenges/list.html')

    def test_profile_view(self):
        # Тест личного кабинета пользователя
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_join_challenge_view(self):
        # Тест присоединения к челленджу
        response = self.client.get(reverse('join_challenge', args=[self.challenge.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('book_selection', args=[self.challenge.id]))

        # Проверим, что участник был добавлен в челлендж
        participant = Participant.objects.get(user=self.user, challenge=self.challenge)
        self.assertIsNotNone(participant)

    def test_book_selection_view(self):
        # Тест страницы выбора книги
        response = self.client.get(reverse('book_selection', args=[self.challenge.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')

    def test_logout_success_view(self):
        # Тест успешного выхода
        response = self.client.get(reverse('logout_success'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'logout_success.html')

    def test_quiz_list_view(self):
        # Тест списка квизов
        response = self.client.get(reverse('quiz_list', args=[self.challenge.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Квиз')
