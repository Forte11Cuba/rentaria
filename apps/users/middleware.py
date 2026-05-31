from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class RentariaAuthMiddleware:
    DASHBOARD_PREFIX = '/dashboard/'
    SUPERADMIN_PREFIX = '/superadmin/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        if not (path.startswith(self.DASHBOARD_PREFIX) or path.startswith(self.SUPERADMIN_PREFIX)):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={path}')

        if request.user.estado != 'active':
            return redirect('/auth/pending/')

        if path.startswith(self.SUPERADMIN_PREFIX) and request.user.rol != 'superadmin':
            return HttpResponseForbidden('Acceso denegado.')

        return self.get_response(request)
