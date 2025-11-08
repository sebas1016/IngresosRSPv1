from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db import transaction
from django.db import IntegrityError
# Create your models here.
ESTADOS_CJOICES = [
    ('pendiente', 'Pendiente por revisión'),
    ('revisado', 'Revisado'),
    ('reparacion', 'En reparación'),
    ('reparado', 'Reparado'),
    ('entregado', 'Entregado'),
    ('devolucion', 'Devolución'),
    ('garantia', 'Garantía'),
]

RECIBIDO_POR_CHOICES = [
    ('alvaro', 'Alvaro Caballero'),
    ('sebastian', 'Sebastián Berrio'),
    ('juan', 'Juan Carlos'),
    ('david', 'David Chavarria'),
]

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    celular = models.CharField(max_length=25)
    referencia = models.CharField(max_length=100) #Como conocio el taller
    
    def __str__(self):
        return f"{self.nombre}"
    
class Equipo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)    
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    serial = models.CharField(max_length=100, blank=True, null=True)
    descripcion_general = models.TextField(blank=True)
    #paga_revision = models.BooleanField(default=False)
    #recibido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    #fecha_ingreso = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.serial or 'sin serial'})"
    
class Ingreso(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    descripcion_dano = models.TextField()
    paga_revision = models.BooleanField(default=False)
    recibido_por = models.CharField(max_length=30, choices=RECIBIDO_POR_CHOICES, default='david')
    estado = models.CharField(max_length=20, choices=ESTADOS_CJOICES, default='pendiente')
    numero_ingreso = models.CharField(max_length=10, unique=True, editable=False, blank=True)
    es_garantia = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Ingreso {self.numero_ingreso}"
    
class HistorialEquipo(models.Model):
    ingreso = models.ForeignKey(Ingreso, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS_CJOICES) #Ej: "En revision", "Reparado", Garantía
    realizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Nuevos campos para el informe técnico
    diagnostico = models.TextField(blank=True, null=True)
    solucion = models.TextField(blank=True, null=True)
    recomendaciones = models.TextField(blank=True, null=True)
    repuestos_usados = models.TextField(blank=True, null=True)
    es_reporte_final = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.estado} - {self.fecha.strftime('%d/%m/%y')}"
    
class ImagenIngreso(models.Model):
    ingreso = models.ForeignKey(Ingreso, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='ingresos/')
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Imagen de ingreso {self.ingreso.numero_ingreso}"
    
class ImagenHistorial(models.Model):
    historial = models.ForeignKey(HistorialEquipo, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='historial/')
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    def __stt__(self):
        return f"Imagen en historial {self.historial}"

class ContadorIngreso(models.Model):
    mes_ano = models.CharField(max_length=6, unique=True)  # Ej: '0725'
    ultimo_numero = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.mes_ano}: {self.ultimo_numero}"
