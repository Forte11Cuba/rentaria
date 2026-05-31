from django.db import models


class Orden(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]
    PAGO_CHOICES = [
        ('bitcoin_btcpay', 'Bitcoin (BTCPay)'),
        ('cash', 'Efectivo'),
    ]

    id = models.CharField(max_length=20, primary_key=True)
    tienda = models.ForeignKey('tiendas.Tienda', on_delete=models.PROTECT, related_name='ordenes')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    dias = models.PositiveIntegerField()
    monto_total_usd = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    payment_id = models.CharField(max_length=200, blank=True)
    contrato_pdf = models.FileField(upload_to='contratos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        ordering = ['-created_at']

    def __str__(self):
        return self.id


class LineaOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='lineas')
    moto = models.ForeignKey('motos.Moto', on_delete=models.PROTECT)
    modelo = models.ForeignKey('motos.ModeloMoto', on_delete=models.PROTECT)
    precio_dia = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal_usd = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Línea de Orden'
        verbose_name_plural = 'Líneas de Orden'


class RespuestaCliente(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='respuestas')
    campo = models.ForeignKey('formularios.CampoFormulario', on_delete=models.PROTECT)
    valor = models.TextField()

    class Meta:
        verbose_name = 'Respuesta de Cliente'
        verbose_name_plural = 'Respuestas de Cliente'
