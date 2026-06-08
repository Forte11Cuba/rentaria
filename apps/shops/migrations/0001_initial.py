import django.db.models.deletion
import django_cryptography.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(unique=True)),
                ('nombre', models.CharField(max_length=200)),
                ('dueno', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tiendas', to=settings.AUTH_USER_MODEL)),
                ('whatsapp_activo', models.BooleanField(default=True)),
                ('whatsapp_numero', models.CharField(blank=True, max_length=20)),
                ('btcpay_activo', models.BooleanField(default=False)),
                ('btcpay_url', models.CharField(blank=True, max_length=500)),
                ('btcpay_api_key', models.CharField(blank=True, max_length=500)),
                ('btcpay_store_id', models.CharField(blank=True, max_length=200)),
                ('btcpay_webhook_secret', models.CharField(blank=True, max_length=500)),
                ('logo', models.ImageField(blank=True, upload_to='logos/')),
                ('activa', models.BooleanField(default=True)),
                ('public_api', models.BooleanField(default=False)),
                ('smtp_host', models.CharField(blank=True, max_length=200)),
                ('smtp_port', models.PositiveIntegerField(default=587)),
                ('smtp_user', models.CharField(blank=True, max_length=200)),
                ('smtp_password', django_cryptography.fields.encrypt(models.CharField(blank=True, max_length=500))),
                ('smtp_use_tls', models.BooleanField(default=True)),
                ('smtp_from_email', models.EmailField(blank=True)),
                ('smtp_from_name', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Shop',
                'verbose_name_plural': 'Shops',
            },
        ),
        migrations.CreateModel(
            name='PlatformSMTPConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('smtp_host', models.CharField(blank=True, max_length=200)),
                ('smtp_port', models.PositiveIntegerField(default=587)),
                ('smtp_user', models.CharField(blank=True, max_length=200)),
                ('smtp_password', django_cryptography.fields.encrypt(models.CharField(blank=True, max_length=500))),
                ('smtp_use_tls', models.BooleanField(default=True)),
                ('smtp_from_email', models.EmailField(blank=True)),
                ('smtp_from_name', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Platform SMTP Config',
            },
        ),
    ]
