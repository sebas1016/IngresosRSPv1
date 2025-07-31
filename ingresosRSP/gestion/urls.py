from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('ingreso/', views.ingreso_equipo, name='ingreso_equipo'),
    path('buscar/', views.buscar_equipo, name='buscar_equipo'),
    path('ingreso/<str:numero_ingreso>/', views.detalle_ingreso, name='detalle_ingreso'),
    path('ingresos/', views.listar_ingresos, name='listar_ingresos'),
    path('api/buscar-ingresos/', views.buscar_ingresos_api, name='buscar_ingresos_api'),
    path('api/ingresos/<int:ingreso_id>/', views.ingreso_detalle_api, name='ingreso_detalle_api'),
    path('api/ingresos/<int:ingreso_id>/actualizar/', views.actualizar_ingreso_api, name='actualizar_ingreso_api'),
    path('reporte-final/<str:numero_ingreso>/', views.reporte_final, name='reporte_final'),
    path('pdf/informe/<str:numero_ingreso>/', views.generar_pdf_informe, name='generar_pdf_informe'),
    path('ingresos/<int:ingreso_id>/pdf/', views.generar_pdf_ingreso, name='pdf_ingreso'),
    path('ingreso-exitoso/<int:ingreso_id>/', views.ingreso_exitoso, name='ingreso_exitoso'),
    path('registro/', views.registro_usuario, name='registro'),
]