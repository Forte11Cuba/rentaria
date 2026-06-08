from django.db import models
from encrypted_model_fields.fields import EncryptedCharField


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
    public_api = models.BooleanField(default=False)
    # SMTP personalizado por tienda
    smtp_host = models.CharField(max_length=200, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_user = models.CharField(max_length=200, blank=True)
    smtp_password = EncryptedCharField(max_length=500, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_from_email = models.EmailField(blank=True)
    smtp_from_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'

    def __str__(self):
        return self.nombre

    def smtp_configured(self):
        return bool(self.smtp_host and self.smtp_user and self.smtp_from_email)


class PlatformSMTPConfig(models.Model):
    smtp_host = models.CharField(max_length=200, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_user = models.CharField(max_length=200, blank=True)
    smtp_password = EncryptedCharField(max_length=500, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_from_email = models.EmailField(blank=True)
    smtp_from_name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Platform SMTP Config'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def is_configured(self):
        return bool(self.smtp_host and self.smtp_user and self.smtp_from_email)
