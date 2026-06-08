from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.shops.models import Shop

from .models import Customer

SESSION_KEY = 'customer_id'


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
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        try:
            customer = Customer.objects.get(email=email, tienda=tienda, is_active=True)
            if customer.check_password(password):
                request.session.cycle_key()
                request.session[SESSION_KEY] = customer.pk
                return redirect('customer_dashboard', slug=slug)
            error = 'Contraseña incorrecta.'
        except Customer.DoesNotExist:
            error = 'No existe una cuenta con ese correo en esta tienda.'

    return render(request, 'customers/login.html', {'tienda': tienda, 'error': error})


@require_POST
def logout(request, slug):
    request.session.pop(SESSION_KEY, None)
    return redirect('customer_login', slug=slug)


def activate(request, slug, token):
    tienda = _get_shop(slug)
    customer = get_object_or_404(Customer, tienda=tienda, activation_token=token, is_active=False)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('password_confirm', '')

        if len(password) < 8:
            return render(request, 'customers/activate.html', {
                'tienda': tienda, 'customer': customer, 'token': token,
                'error': 'La contraseña debe tener al menos 8 caracteres.',
            })
        if password != confirm:
            return render(request, 'customers/activate.html', {
                'tienda': tienda, 'customer': customer, 'token': token,
                'error': 'Las contraseñas no coinciden.',
            })

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
    })


def dashboard(request, slug):
    tienda = _get_shop(slug)
    customer = _current_customer(request, tienda)
    if not customer:
        return redirect('customer_login', slug=slug)

    ordenes = customer.ordenes.order_by('-created_at')
    return render(request, 'customers/dashboard.html', {
        'tienda': tienda, 'customer': customer, 'ordenes': ordenes,
    })
