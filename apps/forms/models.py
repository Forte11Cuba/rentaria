from django.db import models


class FormField(models.Model):
    TIPO_CHOICES = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('email', 'Correo electrónico'),
        ('telefono', 'Teléfono'),
        ('direccion', 'Dirección'),
    ]
    tienda = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='campos')
    etiqueta = models.CharField(max_length=200)
    variable = models.SlugField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    requerido = models.BooleanField(default=True)
    es_email_cliente = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Form Field'
        verbose_name_plural = 'Form Fields'
        unique_together = ('tienda', 'variable')
        ordering = ['orden']

    def __str__(self):
        return self.etiqueta


class ContractTemplate(models.Model):
    tienda = models.OneToOneField(
        'shops.Shop', on_delete=models.CASCADE, related_name='plantillacontrato'
    )
    contenido_md = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contract Template'
        verbose_name_plural = 'Contract Templates'

    def __str__(self):
        return f"Contrato — {self.tienda.nombre}"
