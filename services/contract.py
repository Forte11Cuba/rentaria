import markdown
from django.core.files.base import ContentFile
from django.template import Context, Template


def build_context(orden):
    ctx = {
        'tienda_nombre': orden.tienda.nombre,
        'orden_id': orden.id,
        'fecha_inicio': str(orden.fecha_inicio),
        'fecha_fin': str(orden.fecha_fin),
        'hora_inicio': orden.hora_inicio.strftime('%H:%M') if orden.hora_inicio else '',
        'hora_fin': orden.hora_fin.strftime('%H:%M') if orden.hora_fin else '',
        'lista_cargos': ', '.join(
            f"{cargo.nombre} (${cargo.costo})"
            for l in orden.lineas.prefetch_related('modelo__cargos').all()
            for cargo in l.modelo.cargos.all()
        ),
        'dias': str(orden.dias),
        'monto_total': str(orden.monto_total_usd),
        'lista_motos': ', '.join(
            f"{l.modelo.marca} {l.modelo.modelo} ({l.moto.chapa})"
            for l in orden.lineas.select_related('modelo', 'moto').all()
        ),
        'fecha_contrato': str(orden.created_at.date()),
    }
    for resp in orden.respuestas.select_related('campo').all():
        ctx[resp.campo.variable] = resp.valor
    return ctx


def generate_contract_pdf(orden):
    from weasyprint import HTML

    try:
        md_plantilla = orden.tienda.plantillacontrato.contenido_md
    except Exception:
        md_plantilla = (
            '# Contrato de alquiler\n\n'
            'Shop: {{ tienda_nombre }}\n'
            'Order: {{ orden_id }}\n'
            'Motos: {{ lista_motos }}\n'
            'Desde: {{ fecha_inicio }} — Hasta: {{ fecha_fin }}\n'
            'Total: ${{ monto_total }} USD\n'
            'Fecha: {{ fecha_contrato }}\n'
        )

    contexto = build_context(orden)
    md_renderizado = Template(md_plantilla).render(Context(contexto))
    html_body = markdown.markdown(md_renderizado, extensions=['tables'])

    html_full = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 12pt; color: #111; margin: 2cm; line-height: 1.6; }}
    h1, h2, h3 {{ color: #111; margin-top: 1.5em; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
    td, th {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f5f5f5; }}
    hr {{ border: none; border-top: 1px solid #ccc; margin: 1.5em 0; }}
  </style>
</head>
<body>{html_body}</body>
</html>'''

    pdf_bytes = HTML(string=html_full).write_pdf()
    orden.contrato_pdf.save(f'{orden.id}.pdf', ContentFile(pdf_bytes), save=True)
    return pdf_bytes
