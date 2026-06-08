import logging

from django.conf import settings

import services.smtp as smtp_sender

logger = logging.getLogger(__name__)


def _platform_from():
    return f'{settings.BRAND_NAME} <no-reply@{settings.BASE_DOMAIN}>'


def _generate_ics(orden) -> bytes:
    from datetime import datetime
    from icalendar import Calendar, Event
    cal = Calendar()
    cal.add('prodid', f'-//{settings.BRAND_NAME}//{settings.BASE_DOMAIN}//')
    cal.add('version', '2.0')
    event = Event()
    event.add('summary', f'Renta de moto — {orden.tienda.nombre}')
    if orden.hora_inicio and orden.hora_fin:
        event.add('dtstart', datetime.combine(orden.fecha_inicio, orden.hora_inicio))
        event.add('dtend', datetime.combine(orden.fecha_fin, orden.hora_fin))
    else:
        event.add('dtstart', orden.fecha_inicio)
        event.add('dtend', orden.fecha_fin)
    event.add('description', f'Orden #{orden.id}\nTotal: ${orden.monto_total_usd} USD')
    event.add('uid', f'{orden.id}@{settings.BASE_DOMAIN}')
    cal.add_component(event)
    return cal.to_ical()


def _order_table(orden) -> str:
    motos = ', '.join(
        f"{l.modelo.marca} {l.modelo.modelo}"
        for l in orden.lineas.select_related('modelo').all()
    )
    cargos_rows = ''
    for l in orden.lineas.prefetch_related('modelo__cargos').select_related('modelo').all():
        for cargo in l.modelo.cargos.all():
            cargos_rows += (
                f'<tr><td style="padding:8px 0;color:#6b7280;border-bottom:1px solid #2c2d32">{cargo.nombre}</td>'
                f'<td style="padding:8px 0;color:#e5e5e5;border-bottom:1px solid #2c2d32;text-align:right">${cargo.costo}</td></tr>'
            )
    return f'''
    <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:20px">
      <tr>
        <td style="padding:8px 0;color:#6b7280;border-bottom:1px solid #2c2d32">Order</td>
        <td style="padding:8px 0;color:#e5e5e5;border-bottom:1px solid #2c2d32;text-align:right;font-family:monospace">{orden.id}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6b7280;border-bottom:1px solid #2c2d32">Motos</td>
        <td style="padding:8px 0;color:#e5e5e5;border-bottom:1px solid #2c2d32;text-align:right">{motos}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6b7280;border-bottom:1px solid #2c2d32">Desde</td>
        <td style="padding:8px 0;color:#e5e5e5;border-bottom:1px solid #2c2d32;text-align:right">{orden.fecha_inicio}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6b7280;border-bottom:1px solid #2c2d32">Hasta</td>
        <td style="padding:8px 0;color:#e5e5e5;border-bottom:1px solid #2c2d32;text-align:right">{orden.fecha_fin}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6b7280;border-bottom:1px solid #2c2d32">Hora entrega</td>
        <td style="padding:8px 0;color:#e5e5e5;border-bottom:1px solid #2c2d32;text-align:right">{orden.hora_inicio.strftime('%H:%M') if orden.hora_inicio else '—'}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6b7280;border-bottom:1px solid #2c2d32">Hora devolución</td>
        <td style="padding:8px 0;color:#e5e5e5;border-bottom:1px solid #2c2d32;text-align:right">{orden.hora_fin.strftime('%H:%M') if orden.hora_fin else '—'}</td>
      </tr>
      {cargos_rows}
      <tr>
        <td style="padding:8px 0;color:#6b7280">Total</td>
        <td style="padding:8px 0;color:#f7931a;font-weight:bold;text-align:right;font-family:monospace">${orden.monto_total_usd} USD</td>
      </tr>
    </table>'''


def _base_html(tienda_nombre, titulo, cuerpo) -> str:
    return f'''
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;color:#c9cdd4;background:#1a1b1e;padding:32px">
      <h1 style="color:#f7931a;font-size:18px;margin-bottom:4px;text-transform:uppercase;letter-spacing:4px">{settings.BRAND_NAME.upper()}</h1>
      <p style="color:#6b7280;font-size:12px;margin-top:0;margin-bottom:28px">{tienda_nombre}</p>
      <h2 style="color:#e5e5e5;font-size:17px;margin-bottom:20px">{titulo}</h2>
      {cuerpo}
    </div>'''


# ── Emails de plataforma ───────────────────────────────────────────────────────

def send_account_approved(usuario) -> bool:
    return smtp_sender.send(
        to=usuario.email,
        subject=f'Tu cuenta ha sido aprobada — {settings.BRAND_NAME}',
        html=_base_html(settings.BRAND_NAME, 'Cuenta aprobada', f'''
            <p style="margin-bottom:16px">Hola <strong>{usuario.username}</strong>,</p>
            <p style="margin-bottom:24px">Tu cuenta ha sido aprobada. Ya puedes iniciar sesión y comenzar a configurar tu tienda.</p>
            <a href="{settings.APP_URL}/auth/login/"
               style="display:inline-block;background:#f7931a;color:#1a1b1e;padding:10px 20px;font-weight:600;text-decoration:none;font-size:13px">
              Iniciar sesión →
            </a>'''),
        from_addr=_platform_from(),
    )


def send_account_rejected(usuario) -> bool:
    return smtp_sender.send(
        to=usuario.email,
        subject=f'Actualización sobre tu cuenta — {settings.BRAND_NAME}',
        html=_base_html(settings.BRAND_NAME, 'Solicitud no aprobada', f'''
            <p style="margin-bottom:16px">Hola <strong>{usuario.username}</strong>,</p>
            <p style="margin-bottom:16px">Lamentamos informarte que tu solicitud de cuenta no ha podido ser aprobada en esta ocasión.</p>
            <p style="color:#6b7280;font-size:12px">Si crees que es un error, responde a este correo.</p>'''),
        from_addr=_platform_from(),
    )


# ── Emails de clientes ────────────────────────────────────────────────────────

def send_customer_activation(customer, token, request) -> bool:
    activate_url = request.build_absolute_uri(
        f'/{customer.tienda.slug}/account/activate/{token}/'
    )
    return smtp_sender.send(
        to=customer.email,
        subject=f'Activa tu cuenta — {customer.tienda.nombre}',
        html=_base_html(customer.tienda.nombre, 'Activa tu cuenta', f'''
            <p style="margin-bottom:16px">Tu reserva fue registrada con éxito.</p>
            <p style="margin-bottom:24px">Hemos creado una cuenta para que puedas ver tu historial de reservas. Actívala cuando quieras.</p>
            <a href="{activate_url}"
               style="display:inline-block;background:#f7931a;color:#1a1b1e;padding:10px 20px;font-weight:600;text-decoration:none;font-size:13px">
              Activar mi cuenta →
            </a>
            <p style="color:#6b7280;font-size:11px;margin-top:20px">Si no hiciste esta reserva, ignora este mensaje.</p>'''),
        tienda=customer.tienda,
    )


# ── Emails de reservas ─────────────────────────────────────────────────────────

def send_customer_confirmation(orden) -> bool:
    email_resp = orden.respuestas.filter(campo__es_email_cliente=True).first()
    if not email_resp:
        return False

    ics_data = _generate_ics(orden)
    tabla = _order_table(orden)

    return smtp_sender.send(
        to=email_resp.valor,
        subject=f'Reserva confirmada #{orden.id} — {orden.tienda.nombre}',
        html=_base_html(orden.tienda.nombre, '¡Reserva confirmada!', f'''
            {tabla}
            <p style="color:#6b7280;font-size:12px;margin-top:8px">
              El archivo .ics adjunto te permite agregar la reserva a tu calendario.
            </p>'''),
        tienda=orden.tienda,
        attachments=[{'filename': 'reserva.ics', 'content': list(ics_data)}],
    )


def send_new_order_owner(orden) -> bool:
    metodo = 'Bitcoin (BTCPay)' if orden.metodo_pago == 'bitcoin_btcpay' else 'Efectivo'
    tabla = _order_table(orden)

    return smtp_sender.send(
        to=orden.tienda.dueno.email,
        subject=f'Nueva orden #{orden.id} — {orden.tienda.nombre}',
        html=_base_html(orden.tienda.nombre, 'Nueva orden recibida', f'''
            {tabla}
            <p style="color:#6b7280;font-size:12px;margin-bottom:20px">Método de pago: {metodo}</p>
            <a href="{settings.APP_URL}/dashboard/"
               style="display:inline-block;background:#f7931a;color:#1a1b1e;padding:10px 20px;font-weight:600;text-decoration:none;font-size:13px">
              Ver orden →
            </a>'''),
        from_addr=_platform_from(),
    )


def send_order_confirmed_owner(orden) -> bool:
    tabla = _order_table(orden)

    return smtp_sender.send(
        to=orden.tienda.dueno.email,
        subject=f'Order confirmada #{orden.id} — {orden.tienda.nombre}',
        html=_base_html(orden.tienda.nombre, 'Order confirmada', f'''
            {tabla}
            <a href="{settings.APP_URL}/dashboard/"
               style="display:inline-block;background:#f7931a;color:#1a1b1e;padding:10px 20px;font-weight:600;text-decoration:none;font-size:13px">
              Ver orden →
            </a>'''),
        from_addr=_platform_from(),
    )
