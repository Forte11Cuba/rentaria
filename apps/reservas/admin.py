from django.contrib import admin
from .models import Orden, LineaOrden, RespuestaCliente

admin.site.register(Orden)
admin.site.register(LineaOrden)
admin.site.register(RespuestaCliente)
