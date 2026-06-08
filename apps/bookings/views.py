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

from apps.forms.models import FormField
from apps.units.models import UnitModel, Unit
from apps.shops.models import Shop
from services.btcpay import create_invoice, verify_webhook_signature, verify_payment
from services.confirmation import confirm_order
from services.email import send_new_order_owner, send_customer_activation
from services.whatsapp import generate_whatsapp_link

from apps.customers.models import Customer
from .models import OrderLine, Order, CustomerResponse


HORAS = [f"{h:02d}:00" for h in range(6, 22)]


def _generate_order_id():
    chars = string.ascii_uppercase + string.digits
    return 'BR-' + ''.join(random.choices(chars, k=8))


def _get_shop(slug):
    return get_object_or_404(Shop, slug=slug, activa=True)


def _available_units(modelo, fecha_inicio, fecha_fin):
    ocupadas = Unit.objects.filter(
        modelo=modelo,
        activa=True,
        lineaorden__orden__estado='confirmed',
        lineaorden__orden__fecha_inicio__lt=fecha_fin,
        lineaorden__orden__fecha_fin__gt=fecha_inicio,
    ).values_list('chapa', flat=True)
    return Unit.objects.filter(modelo=modelo, activa=True).exclude(chapa__in=ocupadas)


# ── Step 1: date picker ────────────────────────────────────────────────────────

def step1_dates(request, slug):
    tienda = _get_shop(slug)
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
            return render(request, 'bookings/step1_dates.html', {
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

    return render(request, 'bookings/step1_dates.html', {
        'tienda': tienda, 'today': today.isoformat(),
        'horas': HORAS, 'hi': '09:00', 'hf': '18:00',
    })


# ── Step 2: model selection ────────────────────────────────────────────────────

def step2_models(request, slug):
    tienda = _get_shop(slug)
    sesion = request.session.get('reserva', {})

    if sesion.get('slug') != slug or 'fecha_inicio' not in sesion:
        return redirect('reservas:step1_dates', slug=slug)

    fecha_inicio = date.fromisoformat(sesion['fecha_inicio'])
    fecha_fin = date.fromisoformat(sesion['fecha_fin'])
    dias = (fecha_fin - fecha_inicio).days

    modelos_disponibles = []
    for modelo in UnitModel.objects.filter(tienda=tienda, activo=True).prefetch_related('planes', 'fotos'):
        if dias < modelo.min_dias_alquiler:
            continue
        disp = _available_units(modelo, fecha_inicio, fecha_fin).count()
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
                modelo = UnitModel.objects.get(id=mid, tienda=tienda, activo=True)
            except UnitModel.DoesNotExist:
                continue
            max_disp = _available_units(modelo, fecha_inicio, fecha_fin).count()
            cant = min(cant, max_disp)
            if cant > 0:
                carrito_valido.append({'modelo_id': mid, 'cantidad': cant})

        if not carrito_valido:
            return render(request, 'bookings/step2_models.html', {
                'tienda': tienda, 'modelos_disponibles': modelos_disponibles,
                'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin, 'dias': dias,
                'error': 'Selecciona al menos una moto.',
            })

        sesion['carrito'] = carrito_valido
        sesion['respuestas'] = None
        request.session['reserva'] = sesion
        request.session.modified = True
        return redirect('reservas:step3_form', slug=slug)

    return render(request, 'bookings/step2_models.html', {
        'tienda': tienda, 'modelos_disponibles': modelos_disponibles,
        'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin, 'dias': dias,
    })


# ── Availability endpoint ──────────────────────────────────────────────────────

def availability(request, slug):
    tienda = _get_shop(slug)
    try:
        modelo = UnitModel.objects.get(
            id=request.GET.get('modelo_id'), tienda=tienda, activo=True
        )
        fi = date.fromisoformat(request.GET.get('fecha_inicio', ''))
        ff = date.fromisoformat(request.GET.get('fecha_fin', ''))
    except (UnitModel.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'disponible': False, 'unidades_disponibles': 0})

    disp = _available_units(modelo, fi, ff)
    return JsonResponse({'disponible': disp.exists(), 'unidades_disponibles': disp.count()})


# ── Step 3: client form ────────────────────────────────────────────────────────

def _fields_with_values(campos, valores, errores=None):
    return [
        {
            'campo': c,
            'valor': valores.get(c.variable, ''),
            'error': (errores or {}).get(c.variable, ''),
        }
        for c in campos
    ]


def step3_form(request, slug):
    tienda = _get_shop(slug)
    sesion = request.session.get('reserva', {})

    if sesion.get('slug') != slug or not sesion.get('carrito'):
        return redirect('reservas:step1_dates', slug=slug)

    campos = FormField.objects.filter(tienda=tienda, activo=True).order_by('orden')

    if request.method == 'POST':
        valores = {}
        errores = {}
        for campo in campos:
            v = request.POST.get(campo.variable, '').strip()
            if campo.requerido and not v:
                errores[campo.variable] = f'{campo.etiqueta} es obligatorio.'
            valores[campo.variable] = v

        if errores:
            return render(request, 'bookings/step3_form.html', {
                'tienda': tienda,
                'campos_list': _fields_with_values(campos, valores, errores),
            })

        sesion['respuestas'] = valores
        request.session['reserva'] = sesion
        request.session.modified = True
        return redirect('reservas:step4_payment', slug=slug)

    valores = sesion.get('respuestas') or {}
    return render(request, 'bookings/step3_form.html', {
        'tienda': tienda,
        'campos_list': _fields_with_values(campos, valores),
    })


# ── Step 4: payment method ─────────────────────────────────────────────────────

def step4_payment(request, slug):
    tienda = _get_shop(slug)
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
        modelo = UnitModel.objects.prefetch_related('planes', 'cargos').get(id=item['modelo_id'], tienda=tienda)
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

    return render(request, 'bookings/step4_payment.html', {
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
def book_create(request, slug):
    tienda = _get_shop(slug)
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
            modelo = UnitModel.objects.prefetch_related('planes', 'cargos').get(
                id=item['modelo_id'], tienda=tienda, activo=True
            )
        except UnitModel.DoesNotExist:
            return redirect('reservas:step2_models', slug=slug)

        cant = item['cantidad']
        disponibles = list(_available_units(modelo, fecha_inicio, fecha_fin)[:cant])
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

    orden_id = _generate_order_id()
    while Order.objects.filter(id=orden_id).exists():
        orden_id = _generate_order_id()

    orden = Order.objects.create(
        id=orden_id, tienda=tienda,
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        hora_inicio=hora_inicio, hora_fin=hora_fin,
        dias=dias, monto_total_usd=monto_total,
        metodo_pago=metodo_pago, estado='pending',
    )

    for linea in lineas_data:
        OrderLine.objects.create(
            orden=orden, moto=linea['moto'], modelo=linea['modelo'],
            precio_dia=linea['precio_dia'], subtotal_usd=linea['subtotal'],
        )

    campos = FormField.objects.filter(tienda=tienda, activo=True)
    for campo in campos:
        valor = sesion['respuestas'].get(campo.variable, '')
        if valor:
            CustomerResponse.objects.create(orden=orden, campo=campo, valor=valor)

    # Crear o recuperar cuenta de cliente
    email_resp = orden.respuestas.filter(campo__es_email_cliente=True).first()
    if email_resp:
        customer, created = Customer.objects.get_or_create(
            email=email_resp.valor.strip().lower(),
            tienda=tienda,
        )
        orden.customer = customer
        orden.save(update_fields=['customer'])
        if created:
            token = customer.generate_activation_token()
            try:
                send_customer_activation(customer, token, request)
            except Exception:
                logger.exception('Error enviando email de activación a %s (orden=%s)', customer.email, orden.id)

    del request.session['reserva']
    request.session.modified = True

    # Notificar al dueño de la nueva orden (ambos métodos de pago)
    try:
        send_new_order_owner(orden)
    except Exception:
        pass

    if metodo_pago == 'bitcoin_btcpay':
        checkout_url = ''
        try:
            pago_url = request.build_absolute_uri(
                reverse('reservas:payment_bitcoin', args=[orden_id])
            )
            invoice = create_invoice(tienda, float(monto_total), orden_id, redirect_url=pago_url)
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

    link_wa = generate_whatsapp_link(orden)

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

    return render(request, 'bookings/whatsapp_pending.html', {
        'tienda': tienda, 'orden': orden, 'whatsapp_link': link_wa,
        'lineas_display': lineas_display, 'dias': dias,
    })


# ── Bitcoin payment page ───────────────────────────────────────────────────────

def payment_bitcoin(request, orden_id):
    orden = get_object_or_404(Order, id=orden_id, metodo_pago='bitcoin_btcpay')

    if orden.estado == 'confirmed':
        return redirect('reservas:confirmation', orden_id=orden_id)
    if orden.estado == 'cancelled':
        return render(request, 'bookings/payment_expired.html', {
            'orden': orden, 'tienda': orden.tienda,
        })

    # Verificar BTCPay inmediatamente al cargar (por si ya está pagado al retornar desde BTCPay)
    if orden.payment_id:
        try:
            status = verify_payment(orden.tienda, orden.payment_id)
            logger.info('pago_bitcoin orden=%s btcpay_status=%s', orden_id, status)
            if status in ('Settled', 'Complete', 'Processing'):
                confirm_order(orden)
                return redirect('reservas:confirmation', orden_id=orden_id)
            elif status == 'Expired':
                orden.estado = 'cancelled'
                orden.save(update_fields=['estado'])
                return render(request, 'bookings/payment_expired.html', {
                    'orden': orden, 'tienda': orden.tienda,
                })
        except Exception:
            logger.exception('pago_bitcoin: error verificando BTCPay para orden=%s', orden_id)

    tienda = orden.tienda
    checkout_url = ''
    if orden.payment_id and tienda.btcpay_url:
        checkout_url = f"{tienda.btcpay_url.rstrip('/')}/i/{orden.payment_id}"

    expiry_ts = int((orden.created_at.timestamp() + 30 * 60) * 1000)

    return render(request, 'bookings/payment_bitcoin.html', {
        'orden': orden,
        'tienda': tienda,
        'checkout_url': checkout_url,
        'expiry_ts': expiry_ts,
        'status_url': reverse('reservas:payment_status', args=[orden_id]),
    })


def payment_status(request, orden_id):
    orden = get_object_or_404(Order, id=orden_id)

    if orden.estado == 'confirmed':
        resp = HttpResponse('')
        resp['HX-Redirect'] = reverse('reservas:confirmation', args=[orden_id])
        return resp

    if orden.estado == 'cancelled':
        return render(request, 'bookings/fragments/payment_expired.html', {'orden': orden})

    if orden.payment_id:
        try:
            status = verify_payment(orden.tienda, orden.payment_id)
            logger.info('pago_status orden=%s btcpay_status=%s', orden_id, status)
            if status in ('Settled', 'Complete', 'Processing'):
                confirm_order(orden)
                resp = HttpResponse('')
                resp['HX-Redirect'] = reverse('reservas:confirmation', args=[orden_id])
                return resp
            elif status == 'Expired':
                orden.estado = 'cancelled'
                orden.save(update_fields=['estado'])
                return render(request, 'bookings/fragments/payment_expired.html', {'orden': orden})
        except Exception:
            logger.exception('pago_status: error verificando BTCPay para orden=%s', orden_id)

    return render(request, 'bookings/fragments/payment_pending.html', {
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

    from apps.shops.models import Shop
    try:
        tienda = Shop.objects.get(btcpay_store_id=store_id, activa=True)
    except Shop.DoesNotExist:
        return HttpResponse(status=404)

    if tienda.btcpay_webhook_secret:
        if not verify_webhook_signature(tienda.btcpay_webhook_secret, body, sig_header):
            return HttpResponse(status=401)

    try:
        orden = Order.objects.get(payment_id=invoice_id, estado='pending')
    except Order.DoesNotExist:
        return HttpResponse(status=200)

    try:
        confirm_order(orden)
    except Exception:
        pass

    return HttpResponse(status=200)


# ── Confirmation ───────────────────────────────────────────────────────────────

def confirmation(request, orden_id):
    orden = get_object_or_404(Order, id=orden_id)

    # Si es Bitcoin pendiente, consultar BTCPay para confirmar al instante
    if orden.estado == 'pending' and orden.metodo_pago == 'bitcoin_btcpay' and orden.payment_id:
        try:
            status = verify_payment(orden.tienda, orden.payment_id)
            if status in ('Settled', 'Complete', 'Processing'):
                confirm_order(orden)
                orden.refresh_from_db()
            elif status == 'Expired':
                orden.estado = 'cancelled'
                orden.save(update_fields=['estado'])
                orden.refresh_from_db()
        except Exception:
            pass

    pendiente_btc = (orden.estado == 'pending' and orden.metodo_pago == 'bitcoin_btcpay')
    tiene_contrato = bool(orden.contrato_pdf)
    return render(request, 'bookings/confirmation.html', {
        'orden': orden,
        'tienda': orden.tienda,
        'lineas': orden.lineas.select_related('modelo', 'moto').all(),
        'respuestas': orden.respuestas.select_related('campo').all(),
        'pendiente_btc': pendiente_btc,
        'tiene_contrato': tiene_contrato,
    })


def confirmation_contract_pdf(request, orden_id):
    from services.contract import generate_contract_pdf
    orden = get_object_or_404(Order, id=orden_id, estado='confirmed')
    if not orden.contrato_pdf:
        pdf_bytes = generate_contract_pdf(orden)
        from django.core.files.base import ContentFile
        orden.contrato_pdf.save(f'contrato_{orden_id}.pdf', ContentFile(pdf_bytes), save=True)
    return FileResponse(
        orden.contrato_pdf.open('rb'),
        as_attachment=True,
        filename=f'contrato-{orden_id}.pdf',
    )
