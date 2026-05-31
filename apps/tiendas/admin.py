from django.contrib import admin
from .models import Tienda


@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'dueno', 'activa', 'created_at')
    list_filter = ('activa',)
    search_fields = ('nombre', 'slug', 'dueno__email')
    prepopulated_fields = {'slug': ('nombre',)}
