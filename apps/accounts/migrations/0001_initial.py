import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shops', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cuentas', to='shops.shop')),
                ('nombre', models.CharField(max_length=100)),
                ('moneda', models.CharField(max_length=20)),
                ('activa', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Account',
                'verbose_name_plural': 'Accounts',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cuenta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operaciones', to='accounts.account')),
                ('tipo', models.CharField(choices=[('income', 'Ingreso'), ('expense', 'Gasto'), ('transfer', 'Transferencia')], max_length=20)),
                ('descripcion', models.CharField(blank=True, max_length=500)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=14)),
                ('fecha', models.DateField()),
                ('cuenta_contraparte', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='accounts.account')),
                ('tasa_cambio', models.DecimalField(blank=True, decimal_places=6, max_digits=14, null=True)),
                ('grupo_transferencia', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Operation',
                'verbose_name_plural': 'Operations',
                'ordering': ['-fecha', '-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='account',
            unique_together={('tienda', 'nombre')},
        ),
    ]
