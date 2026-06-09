from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm, SetupForm
from .models import User


class RentariaLoginView(LoginView):
    authentication_form = LoginForm
    template_name = 'auth/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.estado == 'active':
            return redirect(self._role_url(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)
        redirect_url = self.get_redirect_url() or self._role_url(user)
        return HttpResponseRedirect(redirect_url)

    @staticmethod
    def _role_url(user):
        return '/superadmin/' if user.rol == 'superadmin' else '/dashboard/'


def register(request):
    if request.user.is_authenticated and request.user.estado == 'active':
        return redirect('/dashboard/')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pending')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})


def setup(request):
    if User.objects.filter(rol='superadmin').exists():
        return redirect('login')
    if request.method == 'POST':
        form = SetupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('/superadmin/')
    else:
        form = SetupForm()
    return render(request, 'auth/setup.html', {'form': form})


def pending(request):
    return render(request, 'auth/pending.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')
