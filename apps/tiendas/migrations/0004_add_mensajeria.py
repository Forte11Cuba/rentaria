from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tiendas', '0003_tienda_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='tienda',
            name='whatsapp_activo',
            field=models.BooleanField(default=True),
        ),
    ]
