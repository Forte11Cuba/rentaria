from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rentaria', {'fields': ('rol', 'estado')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rentaria', {'fields': ('rol', 'estado')}),
    )
    list_display = ('username', 'email', 'rol', 'estado', 'is_active')
    list_filter = ('rol', 'estado', 'is_active')
