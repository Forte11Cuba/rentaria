from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motos', '0003_planes_seguro'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelomoto',
            name='min_dias_alquiler',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
