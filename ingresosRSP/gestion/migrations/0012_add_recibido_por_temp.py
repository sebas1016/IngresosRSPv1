import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0011_recibidor'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingreso',
            name='recibido_por_temp',
            field=models.ForeignKey(
                to='gestion.recibidor',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                verbose_name='Recibido por',
            ),
        ),
    ]