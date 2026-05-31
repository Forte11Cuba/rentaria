import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tiendas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cuenta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('moneda', models.CharField(max_length=20)),
                ('activa', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cuentas', to='tiendas.tienda')),
            ],
            options={
                'verbose_name': 'Cuenta',
                'verbose_name_plural': 'Cuentas',
                'ordering': ['nombre'],
                'unique_together': {('tienda', 'nombre')},
            },
        ),
        migrations.CreateModel(
            name='Operacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('ingreso', 'Ingreso'), ('gasto', 'Gasto'), ('transferencia', 'Transferencia')], max_length=20)),
                ('descripcion', models.CharField(blank=True, max_length=500)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=14)),
                ('fecha', models.DateField()),
                ('tasa_cambio', models.DecimalField(blank=True, decimal_places=6, max_digits=14, null=True)),
                ('grupo_transferencia', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cuenta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operaciones', to='cuentas.cuenta')),
                ('cuenta_contraparte', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='cuentas.cuenta')),
            ],
            options={
                'verbose_name': 'Operación',
                'verbose_name_plural': 'Operaciones',
                'ordering': ['-fecha', '-created_at'],
            },
        ),
    ]
