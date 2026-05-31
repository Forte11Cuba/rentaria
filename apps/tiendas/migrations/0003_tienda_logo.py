from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tiendas', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tienda',
            name='logo',
            field=models.ImageField(blank=True, upload_to='logos/'),
        ),
    ]
