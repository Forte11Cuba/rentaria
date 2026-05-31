from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
    email_confirm = forms.EmailField(
        required=True,
        label='Confirmar correo electrónico',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'email_confirm', 'password1', 'password2')

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        email_confirm = cleaned_data.get('email_confirm')
        if email and email_confirm and email != email_confirm:
            self.add_error('email_confirm', 'Los correos electrónicos no coinciden.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.rol = 'owner'
        user.estado = 'pending'
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if user.estado == 'pending':
            raise ValidationError(
                'Tu cuenta está pendiente de aprobación. Te notificaremos por email cuando sea revisada.',
                code='pending',
            )
        if user.estado == 'rejected':
            raise ValidationError(
                'Tu cuenta ha sido rechazada. Contacta a soporte si crees que es un error.',
                code='rejected',
            )
        super().confirm_login_allowed(user)
