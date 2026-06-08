import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Customer(models.Model):
    email = models.EmailField()
    nombre = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=128, blank=True)
    tienda = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='clientes')
    activation_token = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('email', 'tienda')
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.email} — {self.tienda.nombre}'

    def generate_activation_token(self):
        self.activation_token = secrets.token_urlsafe(32)
        self.save(update_fields=['activation_token'])
        return self.activation_token

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def total_ordenes(self):
        return self.ordenes.count()
