from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservas', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orden',
            name='hora_inicio',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orden',
            name='hora_fin',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
