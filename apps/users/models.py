from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = [
        ('superadmin', 'Superadmin'),
        ('owner', 'Dueño'),
    ]
    ESTADOS = [
        ('pending', 'Pendiente'),
        ('active', 'Activo'),
        ('rejected', 'Rechazado'),
    ]

    rol = models.CharField(max_length=20, choices=ROLES, default='owner')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pending')

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email or self.username
