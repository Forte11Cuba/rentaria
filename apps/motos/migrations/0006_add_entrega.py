from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motos', '0005_planprecio_diasmin_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelomoto',
            name='seguro_descripcion',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='cargo_extra_activo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='cargo_extra_nombre',
            field=models.CharField(blank=True, default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='cargo_extra_descripcion',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='cargo_extra_costo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
    ]
