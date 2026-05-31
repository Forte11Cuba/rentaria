import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motos', '0001_initial'),
        ('tiendas', '0001_initial'),
        ('reservas', '0001_initial'),  # migration that creates reservas_lineaorden
    ]

    operations = [
        # ── ModeloMoto: add all fields ──────────────────────────────────────
        migrations.AddField(
            model_name='modelomoto',
            name='tienda',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='modelos',
                to='tiendas.tienda',
                default=1,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='marca',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='modelo',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='descripcion',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='precio_dia',
            field=models.DecimalField(decimal_places=2, max_digits=8, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='imagen',
            field=models.ImageField(blank=True, upload_to='motos/'),
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='caracteristicas',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='modelomoto',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterModelOptions(
            name='modelomoto',
            options={
                'ordering': ['marca', 'modelo'],
                'verbose_name': 'Modelo de Moto',
                'verbose_name_plural': 'Modelos de Moto',
            },
        ),

        # ── Moto: replace auto-id with chapa PK + add all fields ───────────
        # Use SeparateDatabaseAndState to handle the PK change safely.
        # The database operations use raw SQL because Django cannot drop the
        # only PK column and replace it in a single operation.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    -- Add chapa column (nullable first so existing rows are valid)
                    ALTER TABLE motos_moto ADD COLUMN chapa VARCHAR(20);

                    -- Drop the old PK constraint and column (CASCADE drops dependent FKs)
                    ALTER TABLE motos_moto DROP CONSTRAINT motos_moto_pkey CASCADE;
                    ALTER TABLE motos_moto DROP COLUMN id;

                    -- Make chapa the new PK
                    ALTER TABLE motos_moto ALTER COLUMN chapa SET NOT NULL;
                    ALTER TABLE motos_moto ADD PRIMARY KEY (chapa);

                    -- Add remaining Moto columns
                    ALTER TABLE motos_moto
                        ADD COLUMN tienda_id INTEGER NOT NULL
                            REFERENCES tiendas_tienda(id) ON DELETE CASCADE
                            DEFERRABLE INITIALLY DEFERRED,
                        ADD COLUMN modelo_id BIGINT NOT NULL
                            REFERENCES motos_modelomoto(id) ON DELETE RESTRICT
                            DEFERRABLE INITIALLY DEFERRED,
                        ADD COLUMN activa BOOLEAN NOT NULL DEFAULT TRUE,
                        ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

                    -- Fix the FK column in reservas_lineaorden that pointed to the old
                    -- integer PK of motos_moto.  The table is empty so type conversion
                    -- is trivial.
                    ALTER TABLE reservas_lineaorden
                        DROP CONSTRAINT IF EXISTS
                            reservas_lineaorden_moto_id_3d5a3e4a_fk_motos_moto_id;
                    ALTER TABLE reservas_lineaorden
                        ALTER COLUMN moto_id TYPE VARCHAR(20);
                    ALTER TABLE reservas_lineaorden
                        ADD CONSTRAINT reservas_lineaorden_moto_id_fk
                        FOREIGN KEY (moto_id)
                        REFERENCES motos_moto(chapa)
                        ON DELETE RESTRICT
                        DEFERRABLE INITIALLY DEFERRED;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                # Remove the auto-generated id field from Django's state
                migrations.RemoveField(model_name='moto', name='id'),
                # Add chapa as PK
                migrations.AddField(
                    model_name='moto',
                    name='chapa',
                    field=models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                # Add remaining fields
                migrations.AddField(
                    model_name='moto',
                    name='tienda',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='motos',
                        to='tiendas.tienda',
                    ),
                ),
                migrations.AddField(
                    model_name='moto',
                    name='modelo',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='motos',
                        to='motos.modelomoto',
                    ),
                ),
                migrations.AddField(
                    model_name='moto',
                    name='activa',
                    field=models.BooleanField(default=True),
                ),
                migrations.AddField(
                    model_name='moto',
                    name='created_at',
                    field=models.DateTimeField(
                        auto_now_add=True,
                        default=django.utils.timezone.now,
                    ),
                    preserve_default=False,
                ),
            ],
        ),
    ]
