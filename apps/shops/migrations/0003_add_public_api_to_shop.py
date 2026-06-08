from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='public_api',
            field=models.BooleanField(default=False),
        ),
    ]
