from django.db import models


class Shop(models.Model):
    slug = models.SlugField(unique=True)
    nombre = models.CharField(max_length=200)
    dueno = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='tiendas')
    whatsapp_activo = models.BooleanField(default=True)
    whatsapp_numero = models.CharField(max_length=20, blank=True)
    btcpay_activo = models.BooleanField(default=False)
    btcpay_url = models.CharField(max_length=500, blank=True)
    btcpay_api_key = models.CharField(max_length=500, blank=True)
    btcpay_store_id = models.CharField(max_length=200, blank=True)
    btcpay_webhook_secret = models.CharField(max_length=500, blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'

    def __str__(self):
        return self.nombre
