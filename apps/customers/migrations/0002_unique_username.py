from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='customer',
            constraint=models.UniqueConstraint(
                condition=models.Q(nombre__gt=''),
                fields=('nombre', 'tienda'),
                name='unique_username_per_shop',
            ),
        ),
    ]
