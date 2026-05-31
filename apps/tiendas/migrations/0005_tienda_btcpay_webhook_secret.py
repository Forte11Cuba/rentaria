from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tiendas', '0004_add_mensajeria'),
    ]

    operations = [
        migrations.AddField(
            model_name='tienda',
            name='btcpay_activo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tienda',
            name='btcpay_webhook_secret',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
