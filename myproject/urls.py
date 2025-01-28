from django.contrib import admin
from challenges import views
from django.conf import settings 
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='logout_success'), name='logout'), 
    path('logout_success/', views.logout_success, name='logout_success'),
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('', include('challenges.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

