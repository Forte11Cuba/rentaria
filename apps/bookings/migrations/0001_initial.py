import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        ('forms', '0001_initial'),
        ('shops', '0001_initial'),
        ('units', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ordenes', to='shops.shop')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ordenes', to='customers.customer')),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('hora_inicio', models.TimeField(blank=True, null=True)),
                ('hora_fin', models.TimeField(blank=True, null=True)),
                ('dias', models.PositiveIntegerField()),
                ('monto_total_usd', models.DecimalField(decimal_places=2, max_digits=8)),
                ('metodo_pago', models.CharField(choices=[('bitcoin_btcpay', 'Bitcoin (BTCPay)'), ('cash', 'Efectivo')], max_length=20)),
                ('estado', models.CharField(choices=[('pending', 'Pendiente'), ('confirmed', 'Confirmada'), ('cancelled', 'Cancelada')], default='pending', max_length=20)),
                ('payment_id', models.CharField(blank=True, max_length=200)),
                ('contrato_pdf', models.FileField(blank=True, upload_to='contratos/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lineas', to='bookings.order')),
                ('moto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='units.unit')),
                ('modelo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='units.unitmodel')),
                ('precio_dia', models.DecimalField(decimal_places=2, max_digits=8)),
                ('subtotal_usd', models.DecimalField(decimal_places=2, max_digits=8)),
            ],
            options={
                'verbose_name': 'Order Line',
                'verbose_name_plural': 'Order Lines',
            },
        ),
        migrations.CreateModel(
            name='CustomerResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respuestas', to='bookings.order')),
                ('campo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='forms.formfield')),
                ('valor', models.TextField()),
            ],
            options={
                'verbose_name': 'Customer Response',
                'verbose_name_plural': 'Customer Responses',
            },
        ),
    ]
