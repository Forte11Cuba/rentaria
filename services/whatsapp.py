from urllib.parse import quote


def generate_whatsapp_link(orden):
    nombre_campo = orden.respuestas.filter(campo__variable='nombre_completo').first()
    nombre = nombre_campo.valor if nombre_campo else 'Cliente'

    motos = '\n'.join(
        f'  - {l.modelo.marca} {l.modelo.modelo}' for l in orden.lineas.all()
    )

    desde = str(orden.fecha_inicio)
    if orden.hora_inicio:
        desde += f' a las {orden.hora_inicio.strftime("%H:%M")}'
    hasta = str(orden.fecha_fin)
    if orden.hora_fin:
        hasta += f' a las {orden.hora_fin.strftime("%H:%M")}'

    mensaje = f"""Hola {orden.tienda.nombre}! Quiero reservar motos.

Motos:
{motos}
Desde: {desde}
Hasta: {hasta}
Total: ${orden.monto_total_usd} USD
Nombre: {nombre}
ID de orden: {orden.id}""".strip()

    return f'https://wa.me/{orden.tienda.whatsapp_numero}?text={quote(mensaje)}'
