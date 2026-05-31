from django.db import models


class CampoFormulario(models.Model):
    TIPO_CHOICES = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('email', 'Correo electrónico'),
        ('telefono', 'Teléfono'),
        ('direccion', 'Dirección'),
    ]
    tienda = models.ForeignKey('tiendas.Tienda', on_delete=models.CASCADE, related_name='campos')
    etiqueta = models.CharField(max_length=200)
    variable = models.SlugField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    requerido = models.BooleanField(default=True)
    es_email_cliente = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Campo de Formulario'
        verbose_name_plural = 'Campos de Formulario'
        unique_together = ('tienda', 'variable')
        ordering = ['orden']

    def __str__(self):
        return self.etiqueta


class PlantillaContrato(models.Model):
    tienda = models.OneToOneField(
        'tiendas.Tienda', on_delete=models.CASCADE, related_name='plantillacontrato'
    )
    contenido_md = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plantilla de Contrato'
        verbose_name_plural = 'Plantillas de Contrato'

    def __str__(self):
        return f"Contrato — {self.tienda.nombre}"
