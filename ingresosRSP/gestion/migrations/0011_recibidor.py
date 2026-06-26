from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0010_remove_imagenhistorial_descripcion_and_more'),  # <-- pon aquí tu última migración real
    ]

    operations = [
        migrations.CreateModel(
            name='Recibidor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Recibidor',
                'verbose_name_plural': 'Recibidores',
                'ordering': ['nombre'],
            },
        ),
    ]