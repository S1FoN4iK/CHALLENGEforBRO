from django.urls import path
from . import views
from .views import support_chat

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('support/', support_chat, name='support_chat'),
    path('', views.challenge_list, name='challenge_list'),
    path('<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('change-password/', views.change_password, name='change_password'),
    path('password-change-done/', views.password_change_done, name='password_change_done'),
    # Ежедневный купон
    path('daily-coupon/', views.get_daily_coupon, name='get_daily_coupon'),

    # Перенаправления на страницы с книгами и квизами
    path('<int:challenge_id>/join/', views.join_challenge, name='join_challenge'),

    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # Список книг и квизов для конкретного челленджа
    path('<int:challenge_id>/books/', views.book_selection, name='book_selection'), 
    path('<int:challenge_id>/quizzes/', views.quiz_list, name='quiz_list'),  
    
    # Страница для деталей книги
    path('<int:book_id>/detail/', views.book_detail, name='book_detail'),
    
    # Страница для прохождения квиза
    path("quiz/<int:quiz_id>/", views.quiz_view, name="quiz_view"),
    # Аудиочелленджи
    path('<int:challenge_id>/audio-challenges/', views.audio_challenge_list, name='audio_challenge_list'), 
    path('audio-challenge/<int:audiochallenge_id>/', views.audio_challenge_detail, name='audio_challenge_detail'),
    path('audio-challenge/<int:audiochallenge_id>/success/', views.audio_challenge_success, name='audio_challenge_success'),
]

