import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Sum


class Cuenta(models.Model):
    tienda = models.ForeignKey(
        'tiendas.Tienda', on_delete=models.CASCADE, related_name='cuentas'
    )
    nombre = models.CharField(max_length=100)
    moneda = models.CharField(max_length=20)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        unique_together = ('tienda', 'nombre')
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'

    def __str__(self):
        return f'{self.nombre} ({self.moneda})'

    @property
    def saldo(self):
        result = self.operaciones.aggregate(total=Sum('monto'))['total']
        return result if result is not None else Decimal('0')


class Operacion(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
        ('transferencia', 'Transferencia'),
    ]
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='operaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=500, blank=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2)  # signed: + entrada, - salida
    fecha = models.DateField()
    # Transfer metadata (nullable — only populated for tipo='transferencia')
    cuenta_contraparte = models.ForeignKey(
        Cuenta, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    tasa_cambio = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    grupo_transferencia = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-created_at']
        verbose_name = 'Operación'
        verbose_name_plural = 'Operaciones'

    def __str__(self):
        return f'{self.cuenta} {self.monto:+}'

    @property
    def es_transferencia(self):
        return self.tipo == 'transferencia'

    @property
    def es_entrada(self):
        return self.monto >= 0
