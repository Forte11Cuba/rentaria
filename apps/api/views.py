from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from apps.shops.models import Shop


def catalog(request, slug):
    shop = get_object_or_404(Shop, slug=slug, activa=True, public_api=True)

    def abs_url(field):
        return request.build_absolute_uri(field.url) if field else None

    modelos = []
    for m in shop.modelos.filter(activo=True).prefetch_related('planes', 'cargos', 'fotos'):
        modelos.append({
            'id': m.id,
            'marca': m.marca,
            'modelo': m.modelo,
            'descripcion': m.descripcion,
            'imagen': abs_url(m.imagen),
            'caracteristicas': m.caracteristicas,
            'min_dias_alquiler': m.min_dias_alquiler,
            'total_unidades': m.unidades_activas(),
            'planes': [
                {'dias_min': p.dias_min, 'dias_max': p.dias_max, 'precio_dia': str(p.precio_dia)}
                for p in m.planes.all()
            ],
            'cargos': [
                {'nombre': c.nombre, 'descripcion': c.descripcion, 'costo': str(c.costo)}
                for c in m.cargos.all()
            ],
            'fotos': [
                {'url': abs_url(f.imagen), 'orden': f.orden}
                for f in m.fotos.all()
                if f.imagen
            ],
        })

    data = {
        'shop': {
            'nombre': shop.nombre,
            'slug': shop.slug,
            'logo': abs_url(shop.logo),
        },
        'modelos': modelos,
    }

    response = JsonResponse(data)
    response['Access-Control-Allow-Origin'] = '*'
    return response
