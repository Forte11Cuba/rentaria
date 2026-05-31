from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('motos', '0006_add_entrega'),
    ]

    operations = [
        migrations.RemoveField(model_name='modelomoto', name='seguro_activo'),
        migrations.RemoveField(model_name='modelomoto', name='seguro_costo'),
        migrations.RemoveField(model_name='modelomoto', name='seguro_descripcion'),
        migrations.RemoveField(model_name='modelomoto', name='cargo_extra_activo'),
        migrations.RemoveField(model_name='modelomoto', name='cargo_extra_nombre'),
        migrations.RemoveField(model_name='modelomoto', name='cargo_extra_descripcion'),
        migrations.RemoveField(model_name='modelomoto', name='cargo_extra_costo'),
        migrations.CreateModel(
            name='CargoMoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True)),
                ('costo', models.DecimalField(decimal_places=2, max_digits=8)),
                ('modelo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cargos',
                    to='motos.modelomoto',
                )),
            ],
            options={
                'verbose_name': 'Cargo adicional',
                'verbose_name_plural': 'Cargos adicionales',
                'ordering': ['id'],
            },
        ),
    ]
