from django.db import models


class Order(models.Model):
    ESTADO_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
    ]
    PAGO_CHOICES = [
        ('bitcoin_btcpay', 'Bitcoin (BTCPay)'),
        ('cash', 'Efectivo'),
    ]

    id = models.CharField(max_length=20, primary_key=True)
    tienda = models.ForeignKey('shops.Shop', on_delete=models.PROTECT, related_name='ordenes')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    dias = models.PositiveIntegerField()
    monto_total_usd = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pending')
    payment_id = models.CharField(max_length=200, blank=True)
    contrato_pdf = models.FileField(upload_to='contratos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return self.id


class OrderLine(models.Model):
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lineas')
    moto = models.ForeignKey('units.Unit', on_delete=models.PROTECT)
    modelo = models.ForeignKey('units.UnitModel', on_delete=models.PROTECT)
    precio_dia = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal_usd = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Order Line'
        verbose_name_plural = 'Order Lines'


class CustomerResponse(models.Model):
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='respuestas')
    campo = models.ForeignKey('forms.FormField', on_delete=models.PROTECT)
    valor = models.TextField()

    class Meta:
        verbose_name = 'Customer Response'
        verbose_name_plural = 'Customer Responses'
