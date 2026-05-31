from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motos', '0004_modelo_min_dias'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planprecio',
            name='dias_min',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
