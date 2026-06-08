from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0003_add_public_api_to_shop'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='email_from_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='shop',
            name='email_from_address',
            field=models.EmailField(blank=True),
        ),
    ]
