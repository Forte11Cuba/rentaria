import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formularios', '0001_initial'),
        ('tiendas', '0001_initial'),
    ]

    operations = [
        # ── CampoFormulario: add all fields ────────────────────────────────
        migrations.AddField(
            model_name='campoformulario',
            name='tienda',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='campos',
                to='tiendas.tienda',
                default=1,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campoformulario',
            name='etiqueta',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campoformulario',
            name='variable',
            field=models.SlugField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campoformulario',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('texto', 'Texto'),
                    ('numero', 'Número'),
                    ('email', 'Correo electrónico'),
                    ('telefono', 'Teléfono'),
                    ('direccion', 'Dirección'),
                ],
                max_length=20,
                default='texto',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campoformulario',
            name='requerido',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='campoformulario',
            name='es_email_cliente',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='campoformulario',
            name='orden',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='campoformulario',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterUniqueTogether(
            name='campoformulario',
            unique_together={('tienda', 'variable')},
        ),
        migrations.AlterModelOptions(
            name='campoformulario',
            options={
                'ordering': ['orden'],
                'verbose_name': 'Campo de Formulario',
                'verbose_name_plural': 'Campos de Formulario',
            },
        ),

        # ── PlantillaContrato: add all fields ──────────────────────────────
        migrations.AddField(
            model_name='plantillacontrato',
            name='tienda',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='plantillacontrato',
                to='tiendas.tienda',
                default=1,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='plantillacontrato',
            name='contenido_md',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='plantillacontrato',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
    ]
