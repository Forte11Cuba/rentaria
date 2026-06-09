from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class RentariaAuthMiddleware:
    DASHBOARD_PREFIX = '/dashboard/'
    SUPERADMIN_PREFIX = '/superadmin/'
    SETUP_PATH = '/auth/setup/'
    SETUP_BYPASS_PREFIXES = ('/static/', '/media/')

    _has_superadmin = False

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        if not type(self)._has_superadmin:
            from apps.users.models import User
            if User.objects.filter(rol='superadmin').exists():
                type(self)._has_superadmin = True
            else:
                if path == self.SETUP_PATH or path.startswith(self.SETUP_BYPASS_PREFIXES):
                    return self.get_response(request)
                return redirect(self.SETUP_PATH)
        elif path == self.SETUP_PATH:
            return redirect('login')

        if not (path.startswith(self.DASHBOARD_PREFIX) or path.startswith(self.SUPERADMIN_PREFIX)):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={path}')

        if request.user.estado != 'active':
            return redirect('/auth/pending/')

        if path.startswith(self.SUPERADMIN_PREFIX) and request.user.rol != 'superadmin':
            return HttpResponseForbidden('Acceso denegado.')

        return self.get_response(request)
