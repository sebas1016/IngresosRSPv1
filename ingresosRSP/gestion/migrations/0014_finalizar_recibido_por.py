from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0013_migrar_datos_recibidor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingreso',
            name='recibido_por',
        ),
        migrations.RenameField(
            model_name='ingreso',
            old_name='recibido_por_temp',
            new_name='recibido_por',
        ),
    ]