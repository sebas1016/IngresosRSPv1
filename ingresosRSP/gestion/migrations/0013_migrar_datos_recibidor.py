from django.db import migrations


def migrar_recibido_por(apps, schema_editor):
    Ingreso = apps.get_model('gestion', 'Ingreso')
    Recibidor = apps.get_model('gestion', 'Recibidor')

    for ingreso in Ingreso.objects.all():
        nombre_texto = (ingreso.recibido_por or '').strip()
        if not nombre_texto:
            continue

        recibidor, _ = Recibidor.objects.get_or_create(nombre=nombre_texto)
        ingreso.recibido_por_temp = recibidor
        ingreso.save(update_fields=['recibido_por_temp'])


def revertir(apps, schema_editor):
    Ingreso = apps.get_model('gestion', 'Ingreso')
    Ingreso.objects.update(recibido_por_temp=None)


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0012_add_recibido_por_temp'),
    ]

    operations = [
        migrations.RunPython(migrar_recibido_por, revertir),
    ]