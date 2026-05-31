from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.reservas.models import Orden
from apps.tiendas.models import Tienda
from apps.usuarios.models import Usuario
from services.email import enviar_cuenta_aprobada, enviar_cuenta_rechazada

from .forms import TiendaSuperadminForm


def dashboard(request):
    context = {
        'total_pendientes': Usuario.objects.filter(rol='dueno', estado='pendiente').count(),
        'total_activos': Usuario.objects.filter(rol='dueno', estado='activo').count(),
        'total_tiendas': Tienda.objects.count(),
        'total_ordenes': Orden.objects.count(),
        'ordenes_confirmadas': Orden.objects.filter(estado='confirmada').count(),
    }
    return render(request, 'superadmin/dashboard.html', context)


def usuarios(request):
    pendientes = Usuario.objects.filter(rol='dueno', estado='pendiente').order_by('-date_joined')
    activos_qs = Usuario.objects.filter(rol='dueno', estado='activo').order_by('username')
    activos_page = Paginator(activos_qs, 50).get_page(request.GET.get('page', 1))
    return render(request, 'superadmin/usuarios.html', {
        'pendientes': pendientes,
        'activos': activos_page,
    })


@require_POST
def usuario_aprobar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, rol='dueno')
    usuario.estado = 'activo'
    usuario.save()
    enviar_cuenta_aprobada(usuario)
    messages.success(request, f'Cuenta de {usuario.username} aprobada.')
    return redirect('superadmin_users')


@require_POST
def usuario_rechazar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, rol='dueno')
    usuario.estado = 'rechazado'
    usuario.save()
    enviar_cuenta_rechazada(usuario)
    messages.success(request, f'Cuenta de {usuario.username} rechazada.')
    return redirect('superadmin_users')


@require_POST
def usuario_eliminar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, rol='dueno')
    username = usuario.username
    try:
        usuario.delete()
        messages.success(request, f'Usuario {username} eliminado.')
    except Exception:
        messages.error(request, f'No se puede eliminar a {username} porque tiene tiendas asociadas.')
    return redirect('superadmin_users')


def usuario_cambiar_password(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, rol='dueno')
    if request.method == 'POST':
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contraseña de {usuario.username} actualizada.')
            return redirect('superadmin_users')
    else:
        form = SetPasswordForm(usuario)
    return render(request, 'superadmin/usuario_cambiar_password.html', {
        'form': form,
        'usuario': usuario,
    })


def tiendas(request):
    todas = Tienda.objects.select_related('dueno').order_by('-created_at')
    return render(request, 'superadmin/tiendas.html', {'tiendas': todas})


def tienda_crear(request):
    if request.method == 'POST':
        form = TiendaSuperadminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tienda creada correctamente.')
            return redirect('superadmin_shops')
    else:
        form = TiendaSuperadminForm()
    return render(request, 'superadmin/tienda_crear.html', {'form': form})


def ordenes(request):
    qs = Orden.objects.select_related('tienda').order_by('-created_at')

    filtro_tienda = request.GET.get('tienda', '')
    filtro_estado = request.GET.get('estado', '')

    if filtro_tienda:
        qs = qs.filter(tienda_id=filtro_tienda)
    if filtro_estado:
        qs = qs.filter(estado=filtro_estado)

    page_obj = Paginator(qs, 25).get_page(request.GET.get('page', 1))
    context = {
        'page_obj': page_obj,
        'tiendas': Tienda.objects.order_by('nombre'),
        'filtro_tienda': filtro_tienda,
        'filtro_estado': filtro_estado,
        'estados': Orden.ESTADO_CHOICES,
    }
    return render(request, 'superadmin/ordenes.html', context)
