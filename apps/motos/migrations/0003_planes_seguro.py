import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motos', '0002_complete_schema'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modelomoto',
            name='precio_dia',
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='seguro_activo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='seguro_costo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.CreateModel(
            name='PlanPrecio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dias_min', models.PositiveIntegerField()),
                ('dias_max', models.PositiveIntegerField(blank=True, null=True)),
                ('precio_dia', models.DecimalField(decimal_places=2, max_digits=8)),
                ('modelo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='planes',
                    to='motos.modelomoto',
                )),
            ],
            options={
                'verbose_name': 'Plan de Precio',
                'verbose_name_plural': 'Planes de Precio',
                'ordering': ['dias_min'],
            },
        ),
    ]
