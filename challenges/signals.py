from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

# Сигнал для создания профиля для нового пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Сигнал для создания профилей для уже существующих пользователей после миграций
@receiver(post_migrate)
def create_profiles_for_existing_users(sender, **kwargs):
    for user in User.objects.all():
        Profile.objects.get_or_create(user=user)
    print("Профили созданы для всех существующих пользователей.")
