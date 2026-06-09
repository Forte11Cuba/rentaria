from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.shops.models import Shop
from services.email import send_customer_password_link

from .models import Customer

SESSION_KEY = 'customer_id'

RECOVER_COOLDOWN_SECONDS = 60
RECOVER_IP_LIMIT = 5
RECOVER_IP_WINDOW = 3600


def _client_ip(request):
    x_real_ip = request.META.get('HTTP_X_REAL_IP', '').strip()
    if x_real_ip:
        return x_real_ip
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', '')


def _get_shop(slug):
    return get_object_or_404(Shop, slug=slug, activa=True)


def _current_customer(request, tienda):
    pk = request.session.get(SESSION_KEY)
    if not pk:
        return None
    try:
        return Customer.objects.get(pk=pk, tienda=tienda, is_active=True)
    except Customer.DoesNotExist:
        return None


def login(request, slug):
    tienda = _get_shop(slug)
    if _current_customer(request, tienda):
        return redirect('customer_dashboard', slug=slug)

    error = None
    if request.method == 'POST':
        identificador = request.POST.get('identificador', '').strip()
        password = request.POST.get('password', '')
        customer = None
        if '@' in identificador:
            customer = Customer.objects.filter(email=identificador.lower(), tienda=tienda, is_active=True).first()
        else:
            matches = Customer.objects.filter(nombre__iexact=identificador, tienda=tienda, is_active=True)
            if matches.count() == 1:
                customer = matches.first()
            elif matches.count() > 1:
                error = 'Hay más de un cliente con ese nombre. Usa tu correo electrónico.'
        if not error:
            if customer and customer.check_password(password):
                request.session.cycle_key()
                request.session[SESSION_KEY] = customer.pk
                return redirect('customer_dashboard', slug=slug)
            elif not error:
                error = 'Usuario o contraseña incorrectos.'

    return render(request, 'customers/login.html', {'tienda': tienda, 'error': error})


@require_POST
def logout(request, slug):
    request.session.pop(SESSION_KEY, None)
    return redirect('customer_login', slug=slug)


def recover(request, slug):
    tienda = _get_shop(slug)
    sent = False
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        ip = _client_ip(request)
        ip_key = f'customer_recover_ip:{ip}'
        cache.add(ip_key, 0, RECOVER_IP_WINDOW)
        ip_count = cache.incr(ip_key)
        if ip_count > RECOVER_IP_LIMIT:
            error = 'Demasiados intentos desde esta red. Intenta de nuevo en una hora.'
        elif not email:
            error = 'Ingresa tu correo electrónico.'
        else:
            email_key = f'customer_recover:{tienda.pk}:{email}'
            if not cache.get(email_key):
                customer = Customer.objects.filter(email=email, tienda=tienda).first()
                if customer:
                    token = customer.generate_activation_token()
                    try:
                        send_customer_password_link(customer, token, request)
                    except Exception:
                        pass
                cache.set(email_key, 1, RECOVER_COOLDOWN_SECONDS)
            sent = True

    return render(request, 'customers/recover.html', {
        'tienda': tienda, 'sent': sent, 'error': error,
    })


def activate(request, slug, token):
    tienda = _get_shop(slug)
    customer = get_object_or_404(Customer, tienda=tienda, activation_token=token)
    is_first_time = not customer.is_active

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('password_confirm', '')

        ctx = {
            'tienda': tienda, 'customer': customer, 'token': token,
            'is_first_time': is_first_time, 'nombre_value': nombre,
        }

        if not nombre:
            ctx['error'] = 'Ingresa un username.'
            return render(request, 'customers/activate.html', ctx)
        if Customer.objects.filter(tienda=tienda, nombre__iexact=nombre).exclude(pk=customer.pk).exists():
            ctx['error'] = 'Ese username ya está en uso en esta tienda.'
            return render(request, 'customers/activate.html', ctx)
        if len(password) < 8:
            ctx['error'] = 'La contraseña debe tener al menos 8 caracteres.'
            return render(request, 'customers/activate.html', ctx)
        if password != confirm:
            ctx['error'] = 'Las contraseñas no coinciden.'
            return render(request, 'customers/activate.html', ctx)

        customer.nombre = nombre
        customer.set_password(password)
        customer.is_active = True
        customer.activation_token = ''
        customer.save()
        request.session.cycle_key()
        request.session[SESSION_KEY] = customer.pk
        return redirect('customer_dashboard', slug=slug)

    return render(request, 'customers/activate.html', {
        'tienda': tienda, 'customer': customer, 'token': token,
        'is_first_time': is_first_time, 'nombre_value': customer.nombre,
    })


def dashboard(request, slug):
    from datetime import date
    from django.contrib.auth.hashers import make_password
    tienda = _get_shop(slug)
    customer = _current_customer(request, tienda)
    if not customer:
        return redirect('customer_login', slug=slug)

    errors = {}
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'perfil':
            nombre = request.POST.get('nombre', '').strip()
            if nombre and Customer.objects.filter(tienda=tienda, nombre__iexact=nombre).exclude(pk=customer.pk).exists():
                errors['nombre'] = 'Ese username ya está en uso en esta tienda.'
            else:
                customer.nombre = nombre
                customer.save(update_fields=['nombre'])
                messages.success(request, 'Nombre actualizado.')
                return redirect('customer_dashboard', slug=slug)
        elif accion == 'password':
            actual = request.POST.get('password_actual', '')
            nueva = request.POST.get('password_nueva', '').strip()
            confirmar = request.POST.get('password_confirmar', '').strip()
            if not customer.check_password(actual):
                errors['password_actual'] = 'Contraseña actual incorrecta.'
            elif len(nueva) < 8:
                errors['password_nueva'] = 'La contraseña debe tener al menos 8 caracteres.'
            elif nueva != confirmar:
                errors['password_confirmar'] = 'Las contraseñas no coinciden.'
            else:
                customer.password = make_password(nueva)
                customer.save(update_fields=['password'])
                messages.success(request, 'Contraseña actualizada.')
                return redirect('customer_dashboard', slug=slug)

    hoy = date.today()
    todas = customer.ordenes.order_by('fecha_inicio')
    proximas = [o for o in todas if o.fecha_fin >= hoy and o.estado != 'cancelled']
    historial = [o for o in todas if o.fecha_fin < hoy or o.estado == 'cancelled']
    historial.sort(key=lambda o: o.fecha_inicio, reverse=True)

    return render(request, 'customers/dashboard.html', {
        'tienda': tienda,
        'customer': customer,
        'proximas': proximas,
        'historial': historial,
        'errors': errors,
    })
