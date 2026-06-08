import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shops', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campos', to='shops.shop')),
                ('etiqueta', models.CharField(max_length=200)),
                ('variable', models.SlugField(max_length=100)),
                ('tipo', models.CharField(choices=[('texto', 'Texto'), ('numero', 'Número'), ('email', 'Correo electrónico'), ('telefono', 'Teléfono'), ('direccion', 'Dirección')], max_length=20)),
                ('requerido', models.BooleanField(default=True)),
                ('es_email_cliente', models.BooleanField(default=False)),
                ('orden', models.PositiveIntegerField(default=0)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Form Field',
                'verbose_name_plural': 'Form Fields',
                'ordering': ['orden'],
            },
        ),
        migrations.CreateModel(
            name='ContractTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tienda', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='plantillacontrato', to='shops.shop')),
                ('contenido_md', models.TextField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Contract Template',
                'verbose_name_plural': 'Contract Templates',
            },
        ),
        migrations.AlterUniqueTogether(
            name='formfield',
            unique_together={('tienda', 'variable')},
        ),
    ]
