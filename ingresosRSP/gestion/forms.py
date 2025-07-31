from django import forms
from .models import (Cliente, Equipo, Ingreso, HistorialEquipo)
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'celular', 'referencia']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'celular': forms.TextInput(attrs={'placeholder': 'Celular'}),
            #'barrio': forms.TextInput(attrs={'placeholder': 'Barrio'}),
            'referencia': forms.TextInput(attrs={'placeholder': 'Referencia o punto de referencia'}),
        }
class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['marca', 'modelo', 'serial', 'descripcion_general']
        widgets = {
            'marca': forms.TextInput(attrs={'placeholder': 'Marca del equipo'}),
            'modelo': forms.TextInput(attrs={'placeholder': 'Modelo'}),
            'serial': forms.TextInput(attrs={'placeholder': 'Serial'}),
            'descripcion_general': forms.Textarea(attrs={
                'placeholder': 'Descripción general del equipo',
                'rows': 3
            }),
        }
    
class IngresoForm(forms.ModelForm):
    class Meta:
        model = Ingreso
        fields = ['descripcion_dano', 'paga_revision', 'es_garantia']
        widgets = {
            'descripcion_dano': forms.Textarea(attrs={
                'placeholder': 'Describa el daño o motivo del ingreso',
                'rows': 3
            }),
        }
class BusquedaForm(forms.Form):
    query = forms.CharField(label='Buscar por nombre, celular o serial', max_length=100)
    
class HistorialForm(forms.ModelForm):
    class Meta:
        model = HistorialEquipo
        fields = ['descripcion', 'estado','costo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'estado': forms.Select(),
        }

class InformeTecnicoForm(forms.ModelForm):
    class Meta:
        model = HistorialEquipo
        fields = ['diagnostico', 'solucion', 'recomendaciones', 'repuestos_usados', 'es_reporte_final']
        
        widgets = {
            'diagnostico': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escriba el diagnóstico técnico'}),
            'solucion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explique la solución'}),
            'recomendaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Recomendaciones para el cliente'}),
            'repuestos_usados': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Indique los repuesdos usados'}),
        }
        
        labels = {
            'diagnostico': 'Diagnóstico Técnico',
            'solucion': 'Solución',
            'recomendaciones': 'Recomendaciones',
            'repuestos_usados': 'Repuestos Usados',
            'es_reporte_final': 'Marcar como informe técnico final',
        }

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password1', 'password2']
        
        labels = {
            'username': 'Username',
            'first_name': 'Nombre',
            'password1': 'Contraseña',
            'password2': 'Confirmar Contraseña'
        }