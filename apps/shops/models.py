from django.core.exceptions import ValidationError
from django.db import models, transaction
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

    def clean(self):
        super().clean()
        if self.slug:
            conflicting = ShopSlugAlias.objects.filter(old_slug=self.slug)
            if self.pk:
                conflicting = conflicting.exclude(shop_id=self.pk)
            if conflicting.exists():
                raise ValidationError({
                    'slug': 'Ese slug fue usado previamente por otra tienda.',
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            previous_slug = None
            if self.pk:
                try:
                    previous_slug = Shop.objects.values_list('slug', flat=True).get(pk=self.pk)
                except Shop.DoesNotExist:
                    previous_slug = None
            super().save(*args, **kwargs)
            if previous_slug and previous_slug != self.slug:
                ShopSlugAlias.objects.update_or_create(
                    old_slug=previous_slug, defaults={'shop': self}
                )
                ShopSlugAlias.objects.filter(old_slug=self.slug, shop=self).delete()


class ShopSlugAlias(models.Model):
    old_slug = models.SlugField(unique=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='slug_aliases')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Shop slug alias'
        verbose_name_plural = 'Shop slug aliases'

    def __str__(self):
        return f'{self.old_slug} → {self.shop.slug}'


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
