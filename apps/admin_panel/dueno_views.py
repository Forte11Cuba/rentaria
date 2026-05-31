import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.cuentas.models import Cuenta, Operacion
from apps.formularios.models import CampoFormulario, PlantillaContrato
from decimal import InvalidOperation

from apps.motos.models import CargoMoto, FotoModelo, ModeloMoto, Moto, PlanPrecio
from apps.reservas.models import LineaOrden, Orden
from apps.tiendas.models import Tienda
from services.confirmacion import confirmar_orden as _confirmar_orden

from .forms import (
    CambiarEmailForm, CampoFormularioForm, CuentaForm, ModeloMotoForm, MotoForm,
    OperacionForm, PlantillaContratoForm, TiendaDuenoForm, TransferenciaForm,
)


def _solo_dueno(request):
    if request.user.rol != 'dueno':
        return HttpResponseForbidden('Acceso denegado.')
    return None


def _tienda_del_dueno(slug, request):
    return get_object_or_404(Tienda, slug=slug, dueno=request.user)


def _tienda_ctx(tienda, request):
    return {
        'tienda': tienda,
        'mis_tiendas': Tienda.objects.filter(dueno=request.user).order_by('nombre'),
    }


# ── Mis tiendas ────────────────────────────────────────────────────────────────

def my_shops(request):
    guard = _solo_dueno(request)
    if guard:
        return guard
    tiendas = Tienda.objects.filter(dueno=request.user).order_by('nombre')
    return render(request, 'admin_panel/my_shops.html', {'tiendas': tiendas})


def settings(request):
    guard = _solo_dueno(request)
    if guard:
        return guard

    accion = request.POST.get('accion') if request.method == 'POST' else None

    if accion == 'email':
        email_form = CambiarEmailForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(request.user)
        if email_form.is_valid():
            email_form.save()
            messages.success(request, 'Correo electrónico actualizado.')
            return redirect('owner_settings')
    elif accion == 'password':
        email_form = CambiarEmailForm(instance=request.user)
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña actualizada.')
            return redirect('owner_settings')
    else:
        email_form = CambiarEmailForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'admin_panel/settings.html', {
        'email_form': email_form,
        'password_form': password_form,
    })


def shop_create(request):
    guard = _solo_dueno(request)
    if guard:
        return guard
    if request.method == 'POST':
        form = TiendaDuenoForm(request.POST)
        if form.is_valid():
            tienda = form.save(commit=False)
            tienda.dueno = request.user
            tienda.save()
            messages.success(request, f'Tienda "{tienda.nombre}" creada.')
            return redirect('owner_inventory', slug=tienda.slug)
    else:
        form = TiendaDuenoForm()
    return render(request, 'admin_panel/shop_create.html', {'form': form})


# ── Inventario ─────────────────────────────────────────────────────────────────

def inventory(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    modelos = ModeloMoto.objects.filter(tienda=tienda).prefetch_related('motos', 'planes')
    ctx = _tienda_ctx(tienda, request)
    ctx['modelos'] = modelos
    return render(request, 'admin_panel/inventory/list.html', ctx)


def _procesar_planes_post(request, modelo):
    """Lee plan_dias_max[] y plan_precio[] del POST y los persiste directamente."""
    dias_max_vals = request.POST.getlist('plan_dias_max')
    precio_vals   = request.POST.getlist('plan_precio')

    planes = []
    for dias_max_str, precio_str in zip(dias_max_vals, precio_vals):
        precio_str   = precio_str.strip()
        dias_max_str = dias_max_str.strip()
        if not precio_str:
            continue
        try:
            precio = Decimal(precio_str)
        except InvalidOperation:
            continue
        dias_max = None
        if dias_max_str:
            try:
                dias_max = int(dias_max_str)
            except ValueError:
                continue
        planes.append({'dias_max': dias_max, 'precio_dia': precio})

    # Ordenar: con límite (por dias_max asc), sin límite al final
    planes.sort(key=lambda p: (p['dias_max'] is None, p['dias_max'] or 0))

    modelo.planes.all().delete()
    prev = 0
    for p in planes:
        PlanPrecio.objects.create(
            modelo=modelo,
            dias_min=prev + 1,
            dias_max=p['dias_max'],
            precio_dia=p['precio_dia'],
        )
        if p['dias_max'] is not None:
            prev = p['dias_max']


def _procesar_cargos_post(request, modelo):
    nombres = request.POST.getlist('cargo_nombre')
    descripciones = request.POST.getlist('cargo_descripcion')
    costos = request.POST.getlist('cargo_costo')

    modelo.cargos.all().delete()
    for nombre, descripcion, costo_str in zip(nombres, descripciones, costos):
        nombre = nombre.strip()
        costo_str = costo_str.strip()
        if not nombre or not costo_str:
            continue
        try:
            costo = Decimal(costo_str)
            if costo < 0:
                continue
        except InvalidOperation:
            continue
        CargoMoto.objects.create(
            modelo=modelo,
            nombre=nombre,
            descripcion=descripcion.strip(),
            costo=costo,
        )


def model_create(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    if request.method == 'POST':
        form = ModeloMotoForm(request.POST, request.FILES)
        if form.is_valid():
            modelo = form.save(commit=False)
            modelo.tienda = tienda
            modelo.save()
            _procesar_planes_post(request, modelo)
            _procesar_cargos_post(request, modelo)
            messages.success(request, f'Modelo {modelo.marca} {modelo.modelo} creado.')
            return redirect('owner_inventory', slug=slug)
    else:
        form = ModeloMotoForm()
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'planes': [], 'cargos': [], 'accion': 'Crear modelo'})
    return render(request, 'admin_panel/inventory/model_form.html', ctx)


def model_edit(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    modelo = get_object_or_404(ModeloMoto, pk=pk, tienda=tienda)
    if request.method == 'POST':
        form = ModeloMotoForm(request.POST, request.FILES, instance=modelo)
        if form.is_valid():
            form.save()
            _procesar_planes_post(request, modelo)
            _procesar_cargos_post(request, modelo)
            messages.success(request, f'Modelo {modelo.marca} {modelo.modelo} actualizado.')
            return redirect('owner_inventory', slug=slug)
    else:
        form = ModeloMotoForm(instance=modelo)
    ctx = _tienda_ctx(tienda, request)
    ctx.update({
        'form': form,
        'planes': modelo.planes.order_by('dias_min'),
        'cargos': modelo.cargos.all(),
        'modelo': modelo,
        'accion': 'Editar modelo',
    })
    return render(request, 'admin_panel/inventory/model_form.html', ctx)


@require_POST
def model_toggle(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    modelo = get_object_or_404(ModeloMoto, pk=pk, tienda=tienda)
    modelo.activo = not modelo.activo
    modelo.save()
    estado = 'activado' if modelo.activo else 'desactivado'
    messages.success(request, f'{modelo.marca} {modelo.modelo} {estado}.')
    return redirect('owner_inventory', slug=slug)


def _sincronizar_imagen_modelo(modelo):
    primera = modelo.fotos.order_by('orden', 'id').first()
    modelo.imagen = primera.imagen if primera else None
    modelo.save(update_fields=['imagen'])


@require_POST
def photo_upload(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    modelo = get_object_or_404(ModeloMoto, pk=pk, tienda=tienda)
    files = request.FILES.getlist('fotos')
    orden_max = max((f.orden for f in modelo.fotos.all()), default=-1)
    for i, f in enumerate(files):
        FotoModelo.objects.create(modelo=modelo, imagen=f, orden=orden_max + i + 1)
    _sincronizar_imagen_modelo(modelo)
    return redirect('owner_model_edit', slug=slug, pk=pk)


@require_POST
def photo_delete(request, slug, pk, foto_pk):
    tienda = _tienda_del_dueno(slug, request)
    modelo = get_object_or_404(ModeloMoto, pk=pk, tienda=tienda)
    foto = get_object_or_404(FotoModelo, pk=foto_pk, modelo=modelo)
    foto.imagen.delete(save=False)
    foto.delete()
    _sincronizar_imagen_modelo(modelo)
    return redirect('owner_model_edit', slug=slug, pk=pk)


@require_POST
def photo_reorder(request, slug, pk, foto_pk):
    tienda = _tienda_del_dueno(slug, request)
    modelo = get_object_or_404(ModeloMoto, pk=pk, tienda=tienda)
    foto = get_object_or_404(FotoModelo, pk=foto_pk, modelo=modelo)
    direccion = request.POST.get('direccion')
    fotos = list(modelo.fotos.order_by('orden', 'id'))
    idx = next((i for i, f in enumerate(fotos) if f.pk == foto.pk), None)
    if idx is None:
        return redirect('owner_model_edit', slug=slug, pk=pk)
    if direccion == 'arriba' and idx > 0:
        fotos[idx].orden, fotos[idx - 1].orden = fotos[idx - 1].orden, fotos[idx].orden
        fotos[idx].save(update_fields=['orden'])
        fotos[idx - 1].save(update_fields=['orden'])
    elif direccion == 'abajo' and idx < len(fotos) - 1:
        fotos[idx].orden, fotos[idx + 1].orden = fotos[idx + 1].orden, fotos[idx].orden
        fotos[idx].save(update_fields=['orden'])
        fotos[idx + 1].save(update_fields=['orden'])
    _sincronizar_imagen_modelo(modelo)
    return redirect('owner_model_edit', slug=slug, pk=pk)


def unit_add(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    if request.method == 'POST':
        form = MotoForm(request.POST, tienda=tienda)
        if form.is_valid():
            moto = form.save(commit=False)
            moto.tienda = tienda
            moto.save()
            messages.success(request, f'Unidad {moto.chapa} agregada.')
            return redirect('owner_inventory', slug=slug)
    else:
        form = MotoForm(tienda=tienda)
    ctx = _tienda_ctx(tienda, request)
    ctx['form'] = form
    return render(request, 'admin_panel/inventory/unit_form.html', ctx)


@require_POST
def unit_toggle(request, slug, chapa):
    tienda = _tienda_del_dueno(slug, request)
    moto = get_object_or_404(Moto, chapa=chapa, tienda=tienda)
    moto.activa = not moto.activa
    moto.save()
    estado = 'activada' if moto.activa else 'desactivada'
    messages.success(request, f'Unidad {moto.chapa} {estado}.')
    return redirect('owner_inventory', slug=slug)


@require_POST
def unit_delete(request, slug, chapa):
    tienda = _tienda_del_dueno(slug, request)
    moto = get_object_or_404(Moto, chapa=chapa, tienda=tienda)
    try:
        moto.delete()
        messages.success(request, f'Chapa {chapa} eliminada.')
    except Exception:
        messages.error(request, f'No se puede eliminar {chapa}: tiene órdenes asociadas.')
    return redirect('owner_inventory', slug=slug)


# ── Formulario ─────────────────────────────────────────────────────────────────

def form(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    campos = CampoFormulario.objects.filter(tienda=tienda).order_by('orden')
    ctx = _tienda_ctx(tienda, request)
    ctx['campos'] = campos
    return render(request, 'admin_panel/form/list.html', ctx)


def field_create(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    if request.method == 'POST':
        form = CampoFormularioForm(request.POST, tienda=tienda)
        if form.is_valid():
            campo = form.save(commit=False)
            campo.tienda = tienda
            campo.orden = CampoFormulario.objects.filter(tienda=tienda).count()
            campo.save()
            messages.success(request, f'Campo "{campo.etiqueta}" creado.')
            return redirect('owner_form', slug=slug)
    else:
        form = CampoFormularioForm(tienda=tienda)
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'accion': 'Agregar campo'})
    return render(request, 'admin_panel/form/field_form.html', ctx)


def field_edit(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    campo = get_object_or_404(CampoFormulario, pk=pk, tienda=tienda)
    if request.method == 'POST':
        form = CampoFormularioForm(request.POST, instance=campo, tienda=tienda)
        if form.is_valid():
            form.save()
            messages.success(request, f'Campo "{campo.etiqueta}" actualizado.')
            return redirect('owner_form', slug=slug)
    else:
        form = CampoFormularioForm(instance=campo, tienda=tienda)
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'campo': campo, 'accion': 'Editar campo'})
    return render(request, 'admin_panel/form/field_form.html', ctx)


@require_POST
def field_delete(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    campo = get_object_or_404(CampoFormulario, pk=pk, tienda=tienda)
    nombre = campo.etiqueta
    campo.delete()
    for i, c in enumerate(CampoFormulario.objects.filter(tienda=tienda).order_by('orden')):
        c.orden = i
        c.save()
    messages.success(request, f'Campo "{nombre}" eliminado.')
    return redirect('owner_form', slug=slug)


@require_POST
def field_reorder(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    try:
        data = json.loads(request.body)
        order = data.get('order', [])
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'ok': False}, status=400)
    for i, campo_id in enumerate(order):
        CampoFormulario.objects.filter(pk=campo_id, tienda=tienda).update(orden=i)
    return JsonResponse({'ok': True})


# ── Contrato ───────────────────────────────────────────────────────────────────

_SYSTEM_VARS = [
    'tienda_nombre', 'orden_id', 'fecha_inicio', 'fecha_fin',
    'dias', 'monto_total', 'lista_motos', 'fecha_contrato',
]


def contract(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    plantilla = PlantillaContrato.objects.filter(tienda=tienda).first()
    campos = CampoFormulario.objects.filter(tienda=tienda, activo=True).order_by('orden')
    form = PlantillaContratoForm(instance=plantilla)
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'plantilla': plantilla, 'campos': campos, 'system_vars': _SYSTEM_VARS})
    return render(request, 'admin_panel/contract/editor.html', ctx)


@require_POST
def contract_save(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    plantilla, _ = PlantillaContrato.objects.get_or_create(
        tienda=tienda, defaults={'contenido_md': ''}
    )
    form = PlantillaContratoForm(request.POST, instance=plantilla)
    if form.is_valid():
        form.save()
        messages.success(request, 'Plantilla del contrato guardada.')
        return redirect('owner_contract', slug=slug)
    campos = CampoFormulario.objects.filter(tienda=tienda, activo=True).order_by('orden')
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'plantilla': plantilla, 'campos': campos, 'system_vars': _SYSTEM_VARS})
    return render(request, 'admin_panel/contract/editor.html', ctx)


# ── Cuentas ────────────────────────────────────────────────────────────────────

def accounts_list(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    cuentas = Cuenta.objects.filter(tienda=tienda).order_by('nombre')
    ctx = _tienda_ctx(tienda, request)
    ctx['cuentas'] = cuentas
    return render(request, 'admin_panel/accounts/list.html', ctx)


def account_create(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.tienda = tienda
            cuenta.save()
            messages.success(request, f'Cuenta "{cuenta.nombre}" creada.')
            return redirect('owner_account_detail', slug=slug, pk=cuenta.pk)
    else:
        form = CuentaForm()
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'accion': 'Nueva cuenta'})
    return render(request, 'admin_panel/accounts/account_form.html', ctx)


def account_edit(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    cuenta = get_object_or_404(Cuenta, pk=pk, tienda=tienda)
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cuenta "{cuenta.nombre}" actualizada.')
            return redirect('owner_account_detail', slug=slug, pk=pk)
    else:
        form = CuentaForm(instance=cuenta)
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'cuenta': cuenta, 'accion': 'Editar cuenta'})
    return render(request, 'admin_panel/accounts/account_form.html', ctx)


def account_detail(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    cuenta = get_object_or_404(Cuenta, pk=pk, tienda=tienda)
    operaciones = (
        Operacion.objects
        .filter(cuenta=cuenta)
        .select_related('cuenta_contraparte')
        .order_by('-fecha', '-created_at')
    )
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'cuenta': cuenta, 'operaciones': operaciones})
    return render(request, 'admin_panel/accounts/detail.html', ctx)


def operation_new(request, slug, pk):
    tienda = _tienda_del_dueno(slug, request)
    cuenta = get_object_or_404(Cuenta, pk=pk, tienda=tienda)
    if request.method == 'POST':
        form = OperacionForm(request.POST)
        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            monto = form.cleaned_data['monto']
            if tipo == 'gasto':
                monto = -monto
            Operacion.objects.create(
                cuenta=cuenta,
                tipo=tipo,
                descripcion=form.cleaned_data['descripcion'],
                monto=monto,
                fecha=form.cleaned_data['fecha'],
            )
            messages.success(request, 'Operación registrada.')
            return redirect('owner_account_detail', slug=slug, pk=pk)
    else:
        form = OperacionForm(initial={'fecha': date.today()})
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'form': form, 'cuenta': cuenta})
    return render(request, 'admin_panel/accounts/operation_form.html', ctx)


@require_POST
def operation_delete(request, slug, op_pk):
    tienda = _tienda_del_dueno(slug, request)
    op = get_object_or_404(Operacion, pk=op_pk, cuenta__tienda=tienda)
    cuenta_pk = op.cuenta_id
    if op.grupo_transferencia:
        Operacion.objects.filter(grupo_transferencia=op.grupo_transferencia).delete()
        messages.success(request, 'Transferencia eliminada.')
    else:
        op.delete()
        messages.success(request, 'Operación eliminada.')
    return redirect('owner_account_detail', slug=slug, pk=cuenta_pk)


def transfer_new(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    if request.method == 'POST':
        form = TransferenciaForm(request.POST, tienda=tienda)
        if form.is_valid():
            d = form.cleaned_data
            origen = d['cuenta_origen']
            destino = d['cuenta_destino']
            monto_origen = d['monto_origen']
            tasa = d['tasa_cambio']
            monto_destino = d['monto_destino'] or (monto_origen * tasa)
            descripcion = d['descripcion'] or f'Transferencia {origen.moneda} → {destino.moneda}'
            fecha = d['fecha']
            grupo = uuid.uuid4()
            with transaction.atomic():
                Operacion.objects.create(
                    cuenta=origen, tipo='transferencia',
                    descripcion=descripcion, monto=-monto_origen, fecha=fecha,
                    cuenta_contraparte=destino, tasa_cambio=tasa,
                    grupo_transferencia=grupo,
                )
                Operacion.objects.create(
                    cuenta=destino, tipo='transferencia',
                    descripcion=descripcion, monto=monto_destino, fecha=fecha,
                    cuenta_contraparte=origen, tasa_cambio=tasa,
                    grupo_transferencia=grupo,
                )
            messages.success(request, f'Transferencia registrada: {monto_origen} {origen.moneda} → {monto_destino} {destino.moneda}.')
            return redirect('owner_accounts', slug=slug)
    else:
        form = TransferenciaForm(tienda=tienda, initial={'fecha': date.today(), 'tasa_cambio': 1})
    ctx = _tienda_ctx(tienda, request)
    ctx['form'] = form
    return render(request, 'admin_panel/accounts/transfer_form.html', ctx)


# ── Dashboard ─────────────────────────────────────────────────────────────────

def dashboard(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    today = date.today()
    inicio_mes = today.replace(day=1)

    ordenes_hoy = Orden.objects.filter(tienda=tienda, created_at__date=today).count()

    ingresos_mes = (
        Orden.objects.filter(tienda=tienda, estado='confirmada', created_at__date__gte=inicio_mes)
        .aggregate(total=Sum('monto_total_usd'))['total'] or Decimal('0')
    )

    motos_en_renta = LineaOrden.objects.filter(
        orden__tienda=tienda,
        orden__estado='confirmada',
        orden__fecha_inicio__lte=today,
        orden__fecha_fin__gte=today,
    ).count()

    pendientes_cash = (
        Orden.objects.filter(tienda=tienda, estado='pendiente', metodo_pago='cash')
        .order_by('-created_at')[:10]
    )

    proximas_entregas = (
        Orden.objects.filter(
            tienda=tienda, estado='confirmada',
            fecha_inicio__gte=today,
            fecha_inicio__lte=today + timedelta(days=7),
        )
        .order_by('fecha_inicio')[:10]
    )

    ctx = _tienda_ctx(tienda, request)
    ctx.update({
        'ordenes_hoy': ordenes_hoy,
        'ingresos_mes': ingresos_mes,
        'motos_en_renta': motos_en_renta,
        'pendientes_cash': pendientes_cash,
        'proximas_entregas': proximas_entregas,
        'today': today,
    })
    return render(request, 'admin_panel/dashboard.html', ctx)


# ── Órdenes ────────────────────────────────────────────────────────────────────

def orders_list(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    estado = request.GET.get('estado', '')

    qs = Orden.objects.filter(tienda=tienda).order_by('-created_at')
    if estado in ('pendiente', 'confirmada', 'cancelada'):
        qs = qs.filter(estado=estado)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    estado_tabs = [('Todas', ''), ('Pendientes', 'pendiente'), ('Confirmadas', 'confirmada'), ('Canceladas', 'cancelada')]
    ctx = _tienda_ctx(tienda, request)
    ctx.update({'page_obj': page_obj, 'estado_filtro': estado, 'estado_tabs': estado_tabs})
    return render(request, 'admin_panel/orders/list.html', ctx)


def order_detail(request, slug, orden_id):
    tienda = _tienda_del_dueno(slug, request)
    orden = get_object_or_404(Orden, id=orden_id, tienda=tienda)
    lineas = orden.lineas.select_related('moto', 'modelo').all()
    respuestas = orden.respuestas.select_related('campo').order_by('campo__orden')

    # Lista de (linea, chapas_disponibles) para el selector de reasignación
    lineas_con_chapas = [
        (
            linea,
            Moto.objects.filter(modelo=linea.modelo, tienda=tienda, activa=True).order_by('chapa')
            if orden.estado != 'cancelada' else [],
        )
        for linea in lineas
    ]

    ctx = _tienda_ctx(tienda, request)
    ctx.update({
        'orden': orden,
        'lineas_con_chapas': lineas_con_chapas,
        'respuestas': respuestas,
    })
    return render(request, 'admin_panel/orders/detail.html', ctx)


@require_POST
def order_confirm(request, slug, orden_id):
    tienda = _tienda_del_dueno(slug, request)
    orden = get_object_or_404(Orden, id=orden_id, tienda=tienda, estado='pendiente', metodo_pago='cash')
    _confirmar_orden(orden)
    messages.success(request, f'Orden {orden.id} confirmada. PDF y emails enviados.')
    return redirect('owner_order_detail', slug=slug, orden_id=orden_id)


@require_POST
def order_cancel(request, slug, orden_id):
    tienda = _tienda_del_dueno(slug, request)
    orden = get_object_or_404(Orden, id=orden_id, tienda=tienda)
    if orden.estado == 'cancelada':
        messages.warning(request, 'La orden ya estaba cancelada.')
        return redirect('owner_order_detail', slug=slug, orden_id=orden_id)
    orden.estado = 'cancelada'
    orden.save(update_fields=['estado'])
    messages.success(request, f'Orden {orden.id} cancelada.')
    return redirect('owner_orders', slug=slug)


@require_POST
def order_reassign(request, slug, orden_id):
    tienda = _tienda_del_dueno(slug, request)
    orden = get_object_or_404(Orden, id=orden_id, tienda=tienda)
    linea = get_object_or_404(LineaOrden, pk=request.POST.get('linea_id'), orden=orden)
    nueva_moto = get_object_or_404(
        Moto, chapa=request.POST.get('nueva_chapa'), modelo=linea.modelo, tienda=tienda
    )
    linea.moto = nueva_moto
    linea.save(update_fields=['moto_id'])
    messages.success(request, f'Chapa reasignada a {nueva_moto.chapa}.')
    return redirect('owner_order_detail', slug=slug, orden_id=orden_id)


def order_contract_pdf(request, slug, orden_id):
    tienda = _tienda_del_dueno(slug, request)
    orden = get_object_or_404(Orden, id=orden_id, tienda=tienda)

    if not orden.contrato_pdf:
        from services.contrato import generar_pdf_contrato
        try:
            generar_pdf_contrato(orden)
        except Exception:
            messages.error(request, 'No se pudo generar el PDF del contrato.')
            return redirect('owner_order_detail', slug=slug, orden_id=orden_id)

    response = FileResponse(orden.contrato_pdf.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="contrato-{orden.id}.pdf"'
    return response


# ── Configuración ──────────────────────────────────────────────────────────────

def shop_settings(request, slug):
    tienda = _tienda_del_dueno(slug, request)
    if request.method == 'POST':
        form = TiendaDuenoForm(request.POST, request.FILES, instance=tienda)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración guardada.')
            return redirect('owner_shop_settings', slug=tienda.slug)
    else:
        form = TiendaDuenoForm(instance=tienda)
    ctx = _tienda_ctx(tienda, request)
    ctx['form'] = form
    return render(request, 'admin_panel/shop_settings.html', ctx)


# ── Calendario ─────────────────────────────────────────────────────────────────

def calendar(request, slug):
    guard = _solo_dueno(request)
    if guard:
        return guard
    tienda = _tienda_del_dueno(slug, request)
    ctx = _tienda_ctx(tienda, request)
    return render(request, 'admin_panel/calendar.html', ctx)


def calendar_events(request, slug):
    guard = _solo_dueno(request)
    if guard:
        return guard
    tienda = _tienda_del_dueno(slug, request)

    try:
        start = date.fromisoformat(request.GET.get('start', '')[:10])
        end = date.fromisoformat(request.GET.get('end', '')[:10])
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)

    ordenes = (
        Orden.objects
        .filter(tienda=tienda, estado='confirmada', fecha_inicio__lt=end, fecha_fin__gte=start)
        .prefetch_related('lineas__modelo', 'lineas__moto', 'respuestas__campo')
    )

    events = []
    for orden in ordenes:
        lineas = list(orden.lineas.all())
        if not lineas:
            continue

        primera = lineas[0]
        titulo = f"{primera.modelo.marca} {primera.modelo.modelo}"
        if len(lineas) > 1:
            titulo += f" +{len(lineas) - 1}"

        hora_i = orden.hora_inicio.strftime('%H:%M') if orden.hora_inicio else '09:00'
        hora_f = orden.hora_fin.strftime('%H:%M') if orden.hora_fin else '18:00'

        events.append({
            'id': f'entrega-{orden.id}',
            'title': f'↓ {titulo}',
            'start': f'{orden.fecha_inicio}T{hora_i}:00',
            'color': '#22c55e',
            'extendedProps': {'tipo': 'entrega', 'orden_id': orden.id},
        })
        events.append({
            'id': f'devolucion-{orden.id}',
            'title': f'↑ {titulo}',
            'start': f'{orden.fecha_fin}T{hora_f}:00',
            'color': '#ef4444',
            'extendedProps': {'tipo': 'devolucion', 'orden_id': orden.id},
        })
        events.append({
            'id': f'renta-{orden.id}',
            'title': titulo,
            'start': orden.fecha_inicio.isoformat(),
            'end': (orden.fecha_fin + timedelta(days=1)).isoformat(),
            'display': 'background',
            'color': '#f7931a',
            'extendedProps': {'tipo': 'renta', 'orden_id': orden.id},
        })

    return JsonResponse(events, safe=False)


def calendar_day(request, slug, dia):
    guard = _solo_dueno(request)
    if guard:
        return guard
    tienda = _tienda_del_dueno(slug, request)

    try:
        dia_date = date.fromisoformat(dia)
    except ValueError:
        from django.http import HttpResponse
        return HttpResponse(status=400)

    ordenes = (
        Orden.objects
        .filter(tienda=tienda, estado='confirmada', fecha_inicio__lte=dia_date, fecha_fin__gte=dia_date)
        .prefetch_related('lineas__modelo', 'lineas__moto', 'respuestas__campo')
    )

    def _cliente(orden):
        r = orden.respuestas.filter(campo__variable='nombre_completo').first()
        return r.valor if r else f'Orden {orden.id}'

    def _enrich(o):
        return {
            'orden': o,
            'cliente': _cliente(o),
            'dias_restantes': (o.fecha_fin - dia_date).days,
        }

    entregas = sorted(
        [_enrich(o) for o in ordenes if o.fecha_inicio == dia_date],
        key=lambda x: x['orden'].hora_inicio or date.min,
    )
    devoluciones = sorted(
        [_enrich(o) for o in ordenes if o.fecha_fin == dia_date],
        key=lambda x: x['orden'].hora_fin or date.min,
    )
    con_clientes = sorted(
        [_enrich(o) for o in ordenes if o.fecha_inicio < dia_date < o.fecha_fin],
        key=lambda x: x['dias_restantes'],
    )

    return render(request, 'admin_panel/calendar_day.html', {
        'dia': dia_date,
        'tienda': tienda,
        'entregas': entregas,
        'devoluciones': devoluciones,
        'con_clientes': con_clientes,
    })
