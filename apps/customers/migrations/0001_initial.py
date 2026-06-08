from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shops', '0005_smtp_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('email', models.EmailField()),
                ('nombre', models.CharField(blank=True, max_length=200)),
                ('password', models.CharField(blank=True, max_length=128)),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clientes', to='shops.shop')),
                ('activation_token', models.CharField(blank=True, max_length=64)),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Customer',
                'verbose_name_plural': 'Customers',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='customer',
            constraint=models.UniqueConstraint(fields=('email', 'tienda'), name='unique_customer_per_shop'),
        ),
    ]
