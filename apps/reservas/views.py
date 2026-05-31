import json
import logging
import random
import string
from datetime import date, time as time_type
from decimal import Decimal

logger = logging.getLogger(__name__)

from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.formularios.models import CampoFormulario
from apps.motos.models import ModeloMoto, Moto
from apps.tiendas.models import Tienda
from services.btcpay import crear_invoice, verificar_firma_webhook, verificar_pago
from services.confirmacion import confirmar_orden
from services.email import enviar_nueva_orden_dueno
from services.whatsapp import generar_link_whatsapp

from .models import LineaOrden, Orden, RespuestaCliente


HORAS = [f"{h:02d}:00" for h in range(6, 22)]


def _generar_id_orden():
    chars = string.ascii_uppercase + string.digits
    return 'BR-' + ''.join(random.choices(chars, k=8))


def _get_tienda(slug):
    return get_object_or_404(Tienda, slug=slug, activa=True)


def _unidades_disponibles(modelo, fecha_inicio, fecha_fin):
    ocupadas = Moto.objects.filter(
        modelo=modelo,
        activa=True,
        lineaorden__orden__estado='confirmada',
        lineaorden__orden__fecha_inicio__lt=fecha_fin,
        lineaorden__orden__fecha_fin__gt=fecha_inicio,
    ).values_list('chapa', flat=True)
    return Moto.objects.filter(modelo=modelo, activa=True).exclude(chapa__in=ocupadas)


# ── Step 1: date picker ────────────────────────────────────────────────────────

def step1_fechas(request, slug):
    tienda = _get_tienda(slug)
    today = date.today()

    if request.method == 'POST':
        fi_str = request.POST.get('fecha_inicio', '')
        ff_str = request.POST.get('fecha_fin', '')
        errores = {}
        fecha_inicio = fecha_fin = None

        try:
            fecha_inicio = date.fromisoformat(fi_str)
        except ValueError:
            errores['fecha_inicio'] = 'Fecha inválida.'

        try:
            fecha_fin = date.fromisoformat(ff_str)
        except ValueError:
            errores['fecha_fin'] = 'Fecha inválida.'

        hi_str = request.POST.get('hora_inicio', '09:00')
        hf_str = request.POST.get('hora_fin', '18:00')

        if fecha_inicio and fecha_inicio < today:
            errores['fecha_inicio'] = 'La fecha de inicio no puede ser en el pasado.'
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            errores['fecha_fin'] = 'La fecha de fin debe ser posterior a la de inicio.'
        if hi_str not in HORAS:
            errores['hora_inicio'] = 'Hora inválida.'
        if hf_str not in HORAS:
            errores['hora_fin'] = 'Hora inválida.'

        if errores:
            return render(request, 'reservas/step1_fechas.html', {
                'tienda': tienda, 'today': today.isoformat(),
                'errores': errores, 'fi': fi_str, 'ff': ff_str,
                'hi': hi_str, 'hf': hf_str, 'horas': HORAS,
            })

        request.session['reserva'] = {
            'slug': slug,
            'fecha_inicio': fi_str,
            'fecha_fin': ff_str,
            'hora_inicio': hi_str,
            'hora_fin': hf_str,
            'carrito': [],
            'respuestas': None,
        }
        return redirect('reservas:step2_models', slug=slug)

    return render(request, 'reservas/step1_fechas.html', {
        'tienda': tienda, 'today': today.isoformat(),
        'horas': HORAS, 'hi': '09:00', 'hf': '18:00',
    })


# ── Step 2: model selection ────────────────────────────────────────────────────

def step2_modelos(request, slug):
    tienda = _get_tienda(slug)
    sesion = request.session.get('reserva', {})

    if sesion.get('slug') != slug or 'fecha_inicio' not in sesion:
        return redirect('reservas:step1_dates', slug=slug)

    fecha_inicio = date.fromisoformat(sesion['fecha_inicio'])
    fecha_fin = date.fromisoformat(sesion['fecha_fin'])
    dias = (fecha_fin - fecha_inicio).days

    modelos_disponibles = []
    for modelo in ModeloMoto.objects.filter(tienda=tienda, activo=True).prefetch_related('planes', 'fotos'):
        if dias < modelo.min_dias_alquiler:
            continue
        disp = _unidades_disponibles(modelo, fecha_inicio, fecha_fin).count()
        if disp > 0:
            plan = modelo.plan_para_dias(dias)
            fotos_galeria = [f.imagen.url for f in modelo.fotos.all()]
        fotos_urls = fotos_galeria if fotos_galeria else ([modelo.imagen.url] if modelo.imagen else [])
        modelos_disponibles.append({
                'modelo': modelo,
                'unidades': disp,
                'plan': plan,
                'precio_dia': plan.precio_dia if plan else None,
                'fotos_json': json.dumps(fotos_urls),
            })

    if request.method == 'POST':
        try:
            carrito = json.loads(request.POST.get('carrito', '[]'))
        except (json.JSONDecodeError, ValueError):
            carrito = []

        carrito_valido = []
        for item in carrito:
            try:
                mid = int(item['modelo_id'])
                cant = int(item['cantidad'])
            except (KeyError, ValueError, TypeError):
                continue
            if cant <= 0:
                continue
            try:
                modelo = ModeloMoto.objects.get(id=mid, tienda=tienda, activo=True)
            except ModeloMoto.DoesNotExist:
                continue
            max_disp = _unidades_disponibles(modelo, fecha_inicio, fecha_fin).count()
            cant = min(cant, max_disp)
            if cant > 0:
                carrito_valido.append({'modelo_id': mid, 'cantidad': cant})

        if not carrito_valido:
            return render(request, 'reservas/step2_modelos.html', {
                'tienda': tienda, 'modelos_disponibles': modelos_disponibles,
                'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin, 'dias': dias,
                'error': 'Selecciona al menos una moto.',
            })

        sesion['carrito'] = carrito_valido
        sesion['respuestas'] = None
        request.session['reserva'] = sesion
        request.session.modified = True
        return redirect('reservas:step3_form', slug=slug)

    return render(request, 'reservas/step2_modelos.html', {
        'tienda': tienda, 'modelos_disponibles': modelos_disponibles,
        'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin, 'dias': dias,
    })


# ── Availability endpoint ──────────────────────────────────────────────────────

def disponibilidad(request, slug):
    tienda = _get_tienda(slug)
    try:
        modelo = ModeloMoto.objects.get(
            id=request.GET.get('modelo_id'), tienda=tienda, activo=True
        )
        fi = date.fromisoformat(request.GET.get('fecha_inicio', ''))
        ff = date.fromisoformat(request.GET.get('fecha_fin', ''))
    except (ModeloMoto.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'disponible': False, 'unidades_disponibles': 0})

    disp = _unidades_disponibles(modelo, fi, ff)
    return JsonResponse({'disponible': disp.exists(), 'unidades_disponibles': disp.count()})


# ── Step 3: client form ────────────────────────────────────────────────────────

def _campos_con_valores(campos, valores, errores=None):
    return [
        {
            'campo': c,
            'valor': valores.get(c.variable, ''),
            'error': (errores or {}).get(c.variable, ''),
        }
        for c in campos
    ]


def step3_formulario(request, slug):
    tienda = _get_tienda(slug)
    sesion = request.session.get('reserva', {})

    if sesion.get('slug') != slug or not sesion.get('carrito'):
        return redirect('reservas:step1_dates', slug=slug)

    campos = CampoFormulario.objects.filter(tienda=tienda, activo=True).order_by('orden')

    if request.method == 'POST':
        valores = {}
        errores = {}
        for campo in campos:
            v = request.POST.get(campo.variable, '').strip()
            if campo.requerido and not v:
                errores[campo.variable] = f'{campo.etiqueta} es obligatorio.'
            valores[campo.variable] = v

        if errores:
            return render(request, 'reservas/step3_formulario.html', {
                'tienda': tienda,
                'campos_list': _campos_con_valores(campos, valores, errores),
            })

        sesion['respuestas'] = valores
        request.session['reserva'] = sesion
        request.session.modified = True
        return redirect('reservas:step4_payment', slug=slug)

    valores = sesion.get('respuestas') or {}
    return render(request, 'reservas/step3_formulario.html', {
        'tienda': tienda,
        'campos_list': _campos_con_valores(campos, valores),
    })


# ── Step 4: payment method ─────────────────────────────────────────────────────

def step4_pago(request, slug):
    tienda = _get_tienda(slug)
    sesion = request.session.get('reserva', {})

    if sesion.get('slug') != slug or not sesion.get('carrito'):
        return redirect('reservas:step1_dates', slug=slug)
    if sesion.get('respuestas') is None:
        return redirect('reservas:step3_form', slug=slug)

    fecha_inicio = date.fromisoformat(sesion['fecha_inicio'])
    fecha_fin = date.fromisoformat(sesion['fecha_fin'])
    dias = (fecha_fin - fecha_inicio).days

    carrito_detalle = []
    monto_total = Decimal('0')

    for item in sesion['carrito']:
        modelo = ModeloMoto.objects.prefetch_related('planes', 'cargos').get(id=item['modelo_id'], tienda=tienda)
        plan = modelo.plan_para_dias(dias)
        precio_dia = plan.precio_dia if plan else Decimal('0')
        subtotal = precio_dia * Decimal(str(item['cantidad'])) * Decimal(str(dias))
        monto_total += subtotal
        cargos_item = []
        for cargo in modelo.cargos.all():
            cargo_subtotal = cargo.costo * Decimal(str(item['cantidad']))
            monto_total += cargo_subtotal
            cargos_item.append({
                'nombre': cargo.nombre,
                'descripcion': cargo.descripcion,
                'subtotal': cargo_subtotal,
            })
        carrito_detalle.append({
            'modelo': modelo, 'cantidad': item['cantidad'],
            'subtotal': subtotal, 'precio_dia': precio_dia, 'plan': plan,
            'cargos': cargos_item,
        })

    return render(request, 'reservas/step4_pago.html', {
        'tienda': tienda,
        'carrito_detalle': carrito_detalle,
        'monto_total': monto_total,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'hora_inicio': sesion.get('hora_inicio', ''),
        'hora_fin': sesion.get('hora_fin', ''),
        'dias': dias,
        'tiene_btcpay': bool(tienda.btcpay_activo and tienda.btcpay_url and tienda.btcpay_api_key and tienda.btcpay_store_id),
        'tiene_whatsapp': bool(tienda.whatsapp_activo and tienda.whatsapp_numero),
    })


# ── Create order ───────────────────────────────────────────────────────────────

@require_POST
def reservar_crear(request, slug):
    tienda = _get_tienda(slug)
    sesion = request.session.get('reserva', {})

    if sesion.get('slug') != slug or not sesion.get('carrito'):
        return redirect('reservas:step1_dates', slug=slug)
    if sesion.get('respuestas') is None:
        return redirect('reservas:step3_form', slug=slug)

    metodo_pago = request.POST.get('metodo_pago')
    if metodo_pago not in ('bitcoin_btcpay', 'cash'):
        return redirect('reservas:step4_payment', slug=slug)

    fecha_inicio = date.fromisoformat(sesion['fecha_inicio'])
    fecha_fin = date.fromisoformat(sesion['fecha_fin'])
    hora_inicio = time_type.fromisoformat(sesion.get('hora_inicio', '09:00'))
    hora_fin = time_type.fromisoformat(sesion.get('hora_fin', '18:00'))
    dias = (fecha_fin - fecha_inicio).days

    lineas_data = []
    monto_total = Decimal('0')

    for item in sesion['carrito']:
        try:
            modelo = ModeloMoto.objects.prefetch_related('planes', 'cargos').get(
                id=item['modelo_id'], tienda=tienda, activo=True
            )
        except ModeloMoto.DoesNotExist:
            return redirect('reservas:step2_models', slug=slug)

        cant = item['cantidad']
        disponibles = list(_unidades_disponibles(modelo, fecha_inicio, fecha_fin)[:cant])
        if len(disponibles) < cant:
            return redirect('reservas:step2_models', slug=slug)

        plan = modelo.plan_para_dias(dias)
        precio_dia = plan.precio_dia if plan else Decimal('0')

        for moto in disponibles:
            subtotal = precio_dia * Decimal(str(dias))
            monto_total += subtotal
            lineas_data.append({
                'moto': moto, 'modelo': modelo,
                'precio_dia': precio_dia, 'subtotal': subtotal,
            })

        for cargo in modelo.cargos.all():
            monto_total += cargo.costo * Decimal(str(cant))

    orden_id = _generar_id_orden()
    while Orden.objects.filter(id=orden_id).exists():
        orden_id = _generar_id_orden()

    orden = Orden.objects.create(
        id=orden_id, tienda=tienda,
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        hora_inicio=hora_inicio, hora_fin=hora_fin,
        dias=dias, monto_total_usd=monto_total,
        metodo_pago=metodo_pago, estado='pendiente',
    )

    for linea in lineas_data:
        LineaOrden.objects.create(
            orden=orden, moto=linea['moto'], modelo=linea['modelo'],
            precio_dia=linea['precio_dia'], subtotal_usd=linea['subtotal'],
        )

    campos = CampoFormulario.objects.filter(tienda=tienda, activo=True)
    for campo in campos:
        valor = sesion['respuestas'].get(campo.variable, '')
        if valor:
            RespuestaCliente.objects.create(orden=orden, campo=campo, valor=valor)

    del request.session['reserva']
    request.session.modified = True

    # Notificar al dueño de la nueva orden (ambos métodos de pago)
    try:
        enviar_nueva_orden_dueno(orden)
    except Exception:
        pass

    if metodo_pago == 'bitcoin_btcpay':
        checkout_url = ''
        try:
            pago_url = request.build_absolute_uri(
                reverse('reservas:payment_bitcoin', args=[orden_id])
            )
            invoice = crear_invoice(tienda, float(monto_total), orden_id, redirect_url=pago_url)
            orden.payment_id = invoice.get('id', '')
            orden.save(update_fields=['payment_id'])
            checkout_url = f"{tienda.btcpay_url.rstrip('/')}/i/{orden.payment_id}"
        except Exception:
            logger.exception('reservar_crear: error creando invoice BTCPay para orden=%s', orden_id)
        # Si el invoice se creó, ir directo a BTCPay; el redirectURL trae al cliente de vuelta
        if checkout_url:
            return redirect(checkout_url)
        # Fallback: mostrar página de pago local si BTCPay falló
        return redirect('reservas:payment_bitcoin', orden_id=orden_id)

    link_wa = generar_link_whatsapp(orden)

    lineas_grouped = {}
    for linea in orden.lineas.select_related('modelo').all():
        key = linea.modelo_id
        if key not in lineas_grouped:
            lineas_grouped[key] = {
                'modelo': linea.modelo, 'cantidad': 0,
                'subtotal': Decimal('0'), 'precio_dia': linea.precio_dia,
            }
        lineas_grouped[key]['cantidad'] += 1
        lineas_grouped[key]['subtotal'] += linea.subtotal_usd

    lineas_display = []
    for data in lineas_grouped.values():
        data['cargos'] = [
            {'nombre': c.nombre, 'descripcion': c.descripcion,
             'subtotal': c.costo * data['cantidad']}
            for c in data['modelo'].cargos.all()
        ]
        lineas_display.append(data)

    return render(request, 'reservas/whatsapp_pendiente.html', {
        'tienda': tienda, 'orden': orden, 'whatsapp_link': link_wa,
        'lineas_display': lineas_display, 'dias': dias,
    })


# ── Bitcoin payment page ───────────────────────────────────────────────────────

def pago_bitcoin(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id, metodo_pago='bitcoin_btcpay')

    if orden.estado == 'confirmada':
        return redirect('reservas:confirmation', orden_id=orden_id)
    if orden.estado == 'cancelada':
        return render(request, 'reservas/pago_expirado.html', {
            'orden': orden, 'tienda': orden.tienda,
        })

    # Verificar BTCPay inmediatamente al cargar (por si ya está pagado al retornar desde BTCPay)
    if orden.payment_id:
        try:
            status = verificar_pago(orden.tienda, orden.payment_id)
            logger.info('pago_bitcoin orden=%s btcpay_status=%s', orden_id, status)
            if status in ('Settled', 'Complete', 'Processing'):
                confirmar_orden(orden)
                return redirect('reservas:confirmation', orden_id=orden_id)
            elif status == 'Expired':
                orden.estado = 'cancelada'
                orden.save(update_fields=['estado'])
                return render(request, 'reservas/pago_expirado.html', {
                    'orden': orden, 'tienda': orden.tienda,
                })
        except Exception:
            logger.exception('pago_bitcoin: error verificando BTCPay para orden=%s', orden_id)

    tienda = orden.tienda
    checkout_url = ''
    if orden.payment_id and tienda.btcpay_url:
        checkout_url = f"{tienda.btcpay_url.rstrip('/')}/i/{orden.payment_id}"

    expiry_ts = int((orden.created_at.timestamp() + 30 * 60) * 1000)

    return render(request, 'reservas/pago_bitcoin.html', {
        'orden': orden,
        'tienda': tienda,
        'checkout_url': checkout_url,
        'expiry_ts': expiry_ts,
        'status_url': reverse('reservas:payment_status', args=[orden_id]),
    })


def pago_status(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)

    if orden.estado == 'confirmada':
        resp = HttpResponse('')
        resp['HX-Redirect'] = reverse('reservas:confirmation', args=[orden_id])
        return resp

    if orden.estado == 'cancelada':
        return render(request, 'reservas/fragments/pago_expired.html', {'orden': orden})

    if orden.payment_id:
        try:
            status = verificar_pago(orden.tienda, orden.payment_id)
            logger.info('pago_status orden=%s btcpay_status=%s', orden_id, status)
            if status in ('Settled', 'Complete', 'Processing'):
                confirmar_orden(orden)
                resp = HttpResponse('')
                resp['HX-Redirect'] = reverse('reservas:confirmation', args=[orden_id])
                return resp
            elif status == 'Expired':
                orden.estado = 'cancelada'
                orden.save(update_fields=['estado'])
                return render(request, 'reservas/fragments/pago_expired.html', {'orden': orden})
        except Exception:
            logger.exception('pago_status: error verificando BTCPay para orden=%s', orden_id)

    return render(request, 'reservas/fragments/pago_pending.html', {
        'orden': orden,
        'status_url': reverse('reservas:payment_status', args=[orden_id]),
    })


# ── BTCPay webhook ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def webhook_btcpay(request):
    body = request.body
    sig_header = request.headers.get('BTCPay-Sig', '')

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse(status=400)

    if data.get('type') not in ('InvoiceSettled', 'InvoicePaymentSettled'):
        return HttpResponse(status=200)

    invoice_id = data.get('invoiceId', '')
    store_id = data.get('storeId', '')
    if not invoice_id or not store_id:
        return HttpResponse(status=400)

    from apps.tiendas.models import Tienda
    try:
        tienda = Tienda.objects.get(btcpay_store_id=store_id, activa=True)
    except Tienda.DoesNotExist:
        return HttpResponse(status=404)

    if tienda.btcpay_webhook_secret:
        if not verificar_firma_webhook(tienda.btcpay_webhook_secret, body, sig_header):
            return HttpResponse(status=401)

    try:
        orden = Orden.objects.get(payment_id=invoice_id, estado='pendiente')
    except Orden.DoesNotExist:
        return HttpResponse(status=200)

    try:
        confirmar_orden(orden)
    except Exception:
        pass

    return HttpResponse(status=200)


# ── Confirmation ───────────────────────────────────────────────────────────────

def confirmacion(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)

    # Si es Bitcoin pendiente, consultar BTCPay para confirmar al instante
    if orden.estado == 'pendiente' and orden.metodo_pago == 'bitcoin_btcpay' and orden.payment_id:
        try:
            status = verificar_pago(orden.tienda, orden.payment_id)
            if status in ('Settled', 'Complete', 'Processing'):
                confirmar_orden(orden)
                orden.refresh_from_db()
            elif status == 'Expired':
                orden.estado = 'cancelada'
                orden.save(update_fields=['estado'])
                orden.refresh_from_db()
        except Exception:
            pass

    pendiente_btc = (orden.estado == 'pendiente' and orden.metodo_pago == 'bitcoin_btcpay')
    tiene_contrato = bool(orden.contrato_pdf)
    return render(request, 'reservas/confirmacion.html', {
        'orden': orden,
        'tienda': orden.tienda,
        'lineas': orden.lineas.select_related('modelo', 'moto').all(),
        'respuestas': orden.respuestas.select_related('campo').all(),
        'pendiente_btc': pendiente_btc,
        'tiene_contrato': tiene_contrato,
    })


def confirmacion_contrato_pdf(request, orden_id):
    from services.contrato import generar_pdf_contrato
    orden = get_object_or_404(Orden, id=orden_id, estado='confirmada')
    if not orden.contrato_pdf:
        pdf_bytes = generar_pdf_contrato(orden)
        from django.core.files.base import ContentFile
        orden.contrato_pdf.save(f'contrato_{orden_id}.pdf', ContentFile(pdf_bytes), save=True)
    return FileResponse(
        orden.contrato_pdf.open('rb'),
        as_attachment=True,
        filename=f'contrato-{orden_id}.pdf',
    )
