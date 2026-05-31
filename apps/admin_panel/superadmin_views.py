from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.bookings.models import Order
from apps.shops.models import Shop
from apps.users.models import User
from services.email import send_account_approved, send_account_rejected

from .forms import ShopSuperadminForm


def dashboard(request):
    context = {
        'total_pendientes': User.objects.filter(rol='owner', estado='pending').count(),
        'total_activos': User.objects.filter(rol='owner', estado='active').count(),
        'total_tiendas': Shop.objects.count(),
        'total_ordenes': Order.objects.count(),
        'ordenes_confirmadas': Order.objects.filter(estado='confirmed').count(),
    }
    return render(request, 'superadmin/dashboard.html', context)


def users(request):
    pendientes = User.objects.filter(rol='owner', estado='pending').order_by('-date_joined')
    activos_qs = User.objects.filter(rol='owner', estado='active').order_by('username')
    activos_page = Paginator(activos_qs, 50).get_page(request.GET.get('page', 1))
    return render(request, 'superadmin/users.html', {
        'pendientes': pendientes,
        'activos': activos_page,
    })


@require_POST
def user_approve(request, pk):
    usuario = get_object_or_404(User, pk=pk, rol='owner')
    usuario.estado = 'active'
    usuario.save()
    send_account_approved(usuario)
    messages.success(request, f'Account de {usuario.username} aprobada.')
    return redirect('superadmin_users')


@require_POST
def user_reject(request, pk):
    usuario = get_object_or_404(User, pk=pk, rol='owner')
    usuario.estado = 'rejected'
    usuario.save()
    send_account_rejected(usuario)
    messages.success(request, f'Account de {usuario.username} rechazada.')
    return redirect('superadmin_users')


@require_POST
def user_delete(request, pk):
    usuario = get_object_or_404(User, pk=pk, rol='owner')
    username = usuario.username
    try:
        usuario.delete()
        messages.success(request, f'User {username} eliminado.')
    except Exception:
        messages.error(request, f'No se puede eliminar a {username} porque tiene tiendas asociadas.')
    return redirect('superadmin_users')


def user_change_password(request, pk):
    usuario = get_object_or_404(User, pk=pk, rol='owner')
    if request.method == 'POST':
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contraseña de {usuario.username} actualizada.')
            return redirect('superadmin_users')
    else:
        form = SetPasswordForm(usuario)
    return render(request, 'superadmin/user_change_password.html', {
        'form': form,
        'usuario': usuario,
    })


def shops(request):
    todas = Shop.objects.select_related('dueno').order_by('-created_at')
    return render(request, 'superadmin/shops.html', {'tiendas': todas})


def shop_create(request):
    if request.method == 'POST':
        form = ShopSuperadminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tienda creada correctamente.')
            return redirect('superadmin_shops')
    else:
        form = ShopSuperadminForm()
    return render(request, 'superadmin/shop_create.html', {'form': form})


def orders(request):
    qs = Order.objects.select_related('tienda').order_by('-created_at')

    filtro_tienda = request.GET.get('tienda', '')
    filtro_estado = request.GET.get('estado', '')

    if filtro_tienda:
        qs = qs.filter(tienda_id=filtro_tienda)
    if filtro_estado:
        qs = qs.filter(estado=filtro_estado)

    page_obj = Paginator(qs, 25).get_page(request.GET.get('page', 1))
    context = {
        'page_obj': page_obj,
        'tiendas': Shop.objects.order_by('nombre'),
        'filtro_tienda': filtro_tienda,
        'filtro_estado': filtro_estado,
        'estados': Order.ESTADO_CHOICES,
    }
    return render(request, 'superadmin/orders.html', context)
