from django.contrib import admin
from .models import Cliente, Equipo, HistorialEquipo
# Register your models here.

@admin.register(Cliente) #Revisar segundo video de pildoras para los filtros de busqueda
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'celular', 'referencia']
    list_filter = ['nombre', 'celular', 'referencia']
    search_fields = ['nombre', 'celular']
    
@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['cliente','marca', 'modelo', 'serial', 'descripcion_general']
    list_filter = ['marca', 'modelo', ]
    search_fields = ['cliente','marca','modelo']
    
@admin.register(HistorialEquipo)
class HistorialEquipoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'descripcion', 'estado']
    list_filter = ['fecha', 'estado']
    search_fields = ['fecha', 'estado']
