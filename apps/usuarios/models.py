from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROLES = [
        ('superadmin', 'Superadmin'),
        ('dueno', 'Dueño'),
    ]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('rechazado', 'Rechazado'),
    ]

    rol = models.CharField(max_length=20, choices=ROLES, default='dueno')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.email or self.username
