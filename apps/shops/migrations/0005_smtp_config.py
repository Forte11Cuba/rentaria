import django_cryptography.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0004_add_email_fields_to_shop'),
    ]

    operations = [
        # Eliminar campos de email simples (reemplazados por SMTP completo)
        migrations.RemoveField(model_name='shop', name='email_from_name'),
        migrations.RemoveField(model_name='shop', name='email_from_address'),
        # Campos SMTP por tienda
        migrations.AddField(
            model_name='shop',
            name='smtp_host',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='shop',
            name='smtp_port',
            field=models.PositiveIntegerField(default=587),
        ),
        migrations.AddField(
            model_name='shop',
            name='smtp_user',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='shop',
            name='smtp_password',
            field=django_cryptography.fields.encrypt(models.CharField(blank=True, max_length=500)),
        ),
        migrations.AddField(
            model_name='shop',
            name='smtp_use_tls',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='shop',
            name='smtp_from_email',
            field=models.EmailField(blank=True),
        ),
        migrations.AddField(
            model_name='shop',
            name='smtp_from_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        # Modelo singleton para SMTP global de la plataforma
        migrations.CreateModel(
            name='PlatformSMTPConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('smtp_host', models.CharField(blank=True, max_length=200)),
                ('smtp_port', models.PositiveIntegerField(default=587)),
                ('smtp_user', models.CharField(blank=True, max_length=200)),
                ('smtp_password', django_cryptography.fields.encrypt(models.CharField(blank=True, max_length=500))),
                ('smtp_use_tls', models.BooleanField(default=True)),
                ('smtp_from_email', models.EmailField(blank=True)),
                ('smtp_from_name', models.CharField(blank=True, max_length=100)),
            ],
            options={'verbose_name': 'Platform SMTP Config'},
        ),
    ]
