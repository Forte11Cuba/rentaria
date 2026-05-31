from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.RentariaLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('pending/', views.pending, name='pending'),
    path('password-reset/', PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.txt',
        subject_template_name='auth/password_reset_subject.txt',
        success_url='/auth/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html',
        success_url='/auth/password-reset/complete/',
    ), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html',
    ), name='password_reset_complete'),
]
