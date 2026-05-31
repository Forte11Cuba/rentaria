from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from .forms import LoginForm, RegistroForm


class RentariaLoginView(LoginView):
    authentication_form = LoginForm
    template_name = 'auth/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.estado == 'activo':
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


def registro(request):
    if request.user.is_authenticated and request.user.estado == 'activo':
        return redirect('/dashboard/')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pending')
    else:
        form = RegistroForm()
    return render(request, 'auth/registro.html', {'form': form})


def espera(request):
    return render(request, 'auth/espera.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')
