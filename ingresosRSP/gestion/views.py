from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClienteForm, EquipoForm, IngresoForm
from .models import Cliente, Equipo, ImagenHistorial, ImagenIngreso, Ingreso, HistorialEquipo,ContadorIngreso, ImagenSerial
from django.db.models import Q, Count, F
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
import json
from django.views.decorators.csrf import csrf_exempt
from .forms import InformeTecnicoForm, RegistroUsuarioForm
from weasyprint import HTML 
from django.db import IntegrityError, transaction
from django.utils.timezone import now
from gestion.models import Ingreso
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from datetime import timedelta
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from django.db.models.functions import TruncMonth

def generar_numero_ingreso():
    año = now().year % 100
    mes = now().month
    base = f"{mes:02}{año:02}"  # Ej: 0725

    with transaction.atomic():
        contador, creado = ContadorIngreso.objects.select_for_update().get_or_create(mes_ano=base)
        contador.ultimo_numero += 1
        contador.save()
        return f"{base}{contador.ultimo_numero:03}"

# Create your views here.

def ingreso_equipo(request):
    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST)
        equipo_form = EquipoForm(request.POST)
        ingreso_form = IngresoForm(request.POST)
        
        if cliente_form.is_valid() and equipo_form.is_valid() and ingreso_form.is_valid():
            #Buscar o crear cliente
            celular = cliente_form.cleaned_data['celular']
            
            cliente, creado =Cliente.objects.get_or_create(
                celular=celular,
                defaults={
                    'nombre': cliente_form.cleaned_data['nombre'],
                    'referencia': cliente_form.cleaned_data['referencia']
                }
                
            )
            #Buscar o crear equipo
            # Buscar o crear equipo
            marca = equipo_form.cleaned_data['marca']
            if marca == 'Otra':
                marca = request.POST.get('marca_otro')

            equipo, creado = Equipo.objects.get_or_create(
                cliente=cliente,
                marca=marca,
                modelo=equipo_form.cleaned_data['modelo'],
                serial=equipo_form.cleaned_data['serial'],
                defaults={
                    'descripcion_general': equipo_form.cleaned_data['descripcion_general']
                }
            )

            
            #Crear nuevo ingreso
            try:
                with transaction.atomic():
                    ingreso = ingreso_form.save(commit=False)
                    ingreso.numero_ingreso = generar_numero_ingreso()
                    ingreso.equipo = equipo

                    if ingreso.es_garantia:
                        ingreso.estado = 'garantia'
                    elif ingreso.estado == 'garantia':
                        ingreso.estado = 'pendiente'

                    ingreso.save()
            
                    # Guardar Imágenes del Ingreso
                    imagenes = request.FILES.getlist('imagenes')
                    for img in imagenes:
                        ImagenIngreso.objects.create(ingreso=ingreso, imagen=img)

                    #Guardar imagenes del serial
                    imagenes_serial = request.FILES.getlist('imagenes_serial')
                    for img in imagenes_serial:
                        ImagenSerial.objects.create(equipo=equipo, imagen=img)
                        
            except IntegrityError:
                return HttpResponse("Error al guardar el ingreso. Intenta de nuevo.", status=500)     

            return redirect('ingreso_exitoso', ingreso_id=ingreso.id)

            #return redirect('ingreso_equipo')
            
    else:
        cliente_form = ClienteForm()
        equipo_form = EquipoForm()
        ingreso_form = IngresoForm()
            
    return render(request, 'gestion/ingreso_equipo.html', {
        'cliente_form': cliente_form,
        'equipo_form': equipo_form,
        'ingreso_form': ingreso_form,
        })
    

def detalle_ingreso(request, numero_ingreso):
    ingreso = get_object_or_404(Ingreso, numero_ingreso=numero_ingreso)
    equipo = ingreso.equipo
    cliente = ingreso.equipo.cliente
    historial = HistorialEquipo.objects.filter(ingreso=ingreso).order_by('-fecha')
    imagenes = ingreso.imagenes.all()
    imagenes_serial = equipo.imagenes_serial.all()
    
    from .forms import HistorialForm
    
    if request.method == 'POST':
        form = HistorialForm(request.POST)
        if form.is_valid():
            historial_item = form.save(commit=False)
            historial_item.ingreso = ingreso
            historial_item.realizado_por = None
            ingreso.estado = historial_item.estado
            ingreso.save()
            historial_item.save()
            
            # Captura múltiples imágenes del input llamado "imagen"
            for img in request.FILES.getlist('imagen'):
                ImagenHistorial.objects.create(historial=historial_item, imagen=img)

            return redirect('detalle_ingreso', numero_ingreso=numero_ingreso)
    else:
        form = HistorialForm()
    
    return render(request, 'gestion/detalle_ingreso.html', {
        'ingreso': ingreso,
        'equipo': equipo,
        'cliente': cliente,
        'historial': historial,
        'imagenes': imagenes,
        'imagenes_serial': imagenes_serial,
        'form':form,
    })

def listar_ingresos(request):
    estado_filtrado = request.GET.get('estado')
    busqueda = request.GET.get('query')
    
    ingresos = Ingreso.objects.select_related('equipo__cliente').order_by('-fecha_ingreso')
    if estado_filtrado:
        ingresos = Ingreso.objects.filter(estado=estado_filtrado).order_by('-fecha_ingreso')
    
    if busqueda:
        ingresos = ingresos.filter(
            Q(numero_ingreso__icontains=busqueda) | 
            Q(equipo__cliente__nombre__icontains=busqueda) |
            Q(equipo__cliente__celular__icontains=busqueda) |
            Q(equipo__modelo__icontains=busqueda) |
            Q(equipo__marca__icontains=busqueda)
        )
    else:
        ingresos = Ingreso.objects.all().order_by('-fecha_ingreso')
        
    return render(request, 'gestion/listar_ingresos.html', {
        'ingresos': ingresos,
        'estado_filtrado':estado_filtrado,
        'busqueda':busqueda
    })

def buscar_ingresos_api(request):
    """
    API para buscar ingresos con filtros por estado, búsqueda y alertas
    Las alertas ahora se basan en días hábiles (excluyendo fines de semana)
    """
    busqueda = request.GET.get('query','')
    estado = request.GET.get('estado','')
    alerta = request.GET.get('alerta','')
    
    ingresos = Ingreso.objects.select_related('equipo__cliente').order_by('-fecha_ingreso')
    
    #Filtro por estado
    if estado:
        ingresos = ingresos.filter(estado=estado)
    
    #Filtro por busquda de texto
    if busqueda:
        ingresos = ingresos.filter(
            Q(numero_ingreso__icontains=busqueda) |
            Q(equipo__cliente__nombre__icontains=busqueda) |
            Q(equipo__cliente__celular__icontains=busqueda) |
            Q(equipo__modelo__icontains=busqueda) |
            Q(equipo__marca__icontains=busqueda)
        )
    
    #Filtro por nivel de alerta
    if alerta:
        #Primero filtramos solo pendientes
        ingresos = ingresos.filter(estado='pendiente')
        
        #Aplicamos el filtro de dias en python
        #la logica de días hábiles es compleja para sql
        ingresos_list = list(ingresos)
        
        if alerta == 'green':
            ingresos_filtrados = [
                ing for ing in ingresos_list
                if ing.dias_en_taller() < 6
            ]
        elif alerta == 'con-alerta':
            ingresos_filtrados = [
                ing for ing in ingresos_list
                if ing.dias_en_taller() >5 and ing.dias_en_taller() <=8
            ]
        elif alerta == 'critico':
            ingresos_filtrados = [
                ing for ing in ingresos_list
                if ing.dias_en_taller() > 8
            ]
        else:
            ingresos_filtrados=ingresos_list
    
        
        html = render_to_string('gestion/fragmento_tabla_ingresos.html', {
            'ingresos':ingresos_filtrados
            })
    else:
        html = render_to_string('gestion/fragmento_tabla_ingresos.html', {
            'ingresos':ingresos
            })
    return JsonResponse({'html':html})  

def calcular_dias_habiles_entre_fechas(fecha_inicio, fecha_fin):
    """
    Calcula los días hábiles entre dos fechas (excluye sábados y domingos)
    Útil para cálculos en vistas y reportes
    """
    from datetime import timedelta
    
    dias_habiles = 0
    fecha_actual = fecha_inicio.date() if hasattr(fecha_inicio, 'date') else fecha_inicio
    fecha_final = fecha_fin.date() if hasattr(fecha_fin, 'date') else fecha_fin
    
    while fecha_actual <= fecha_final:
        # weekday(): 0=Lunes, 1=Martes, ..., 4=Viernes, 5=Sábado, 6=Domingo
        if fecha_actual.weekday() < 5:
            dias_habiles += 1
        fecha_actual += timedelta(days=1)
    
    return max(0, dias_habiles - 1)
   
def ingreso_detalle_api(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso.objects.select_related('equipo__cliente'), id=ingreso_id)
    historial = HistorialEquipo.objects.filter(ingreso=ingreso).select_related('realizado_por').order_by('fecha')
    
    data = {
        'numero_ingreso': ingreso.numero_ingreso,
        'fecha_ingreso': ingreso.fecha_ingreso.isoformat(),
        'descripcion_dano': ingreso.descripcion_dano,
        'paga_revision': ingreso.paga_revision,
        'estado': ingreso.estado,
        'recibido_por': ingreso.get_recibido_por_display(),
        'es_garantia': ingreso.estado == 'garantia',
        'cliente': {
            'nombre': ingreso.equipo.cliente.nombre,
            'celular': ingreso.equipo.cliente.celular,
            'referencia': ingreso.equipo.cliente.referencia,
        },
        'equipo': {
            'marca': ingreso.equipo.marca,
            'modelo': ingreso.equipo.modelo,
            'serial': ingreso.equipo.serial,
            'descripcion_general': ingreso.equipo.descripcion_general,
        },
        'historial': [
            {
                'fecha': h.fecha.isoformat(),
                'descripcion': h.descripcion,
                'estado': h.estado,
                'realizado_por': h.realizado_por.get_full_name() if h.realizado_por else "—",
                'costo': float(h.costo) if h.costo else None,
            } for h in historial
        ]
    }
    return JsonResponse(data)

@csrf_exempt  # temporalmente, o maneja CSRF si usas SessionMiddleware
def actualizar_ingreso_api(request, ingreso_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    ingreso = get_object_or_404(Ingreso, id=ingreso_id)
    data = json.loads(request.body)

    ingreso.descripcion_dano = data.get('descripcion_dano', '')
    ingreso.estado = data.get('estado', ingreso.estado)
    ingreso.paga_revision = data.get('paga_revision', False)
    ingreso.es_garantia = data.get('es_garantia', False)
    ingreso.save()

    return JsonResponse({'success': True})


def inicio(request):
    return render(request, 'gestion/inicio.html')

#Reporte Tecnico (PDF)
def reporte_final(request, numero_ingreso):
    ingreso = get_object_or_404(Ingreso, numero_ingreso=numero_ingreso)
    equipo = ingreso.equipo
    cliente = equipo.cliente
    
    if request.method == "POST":
        form = InformeTecnicoForm(request.POST)
        if form.is_valid():
            historial = form.save(commit=False)
            historial.ingreso = ingreso
            historial.realizado_por = request.user
            #historial.estado = ingreso.estado
            historial.save()
            
            #actualizar estado del ingreso con el nuevo estado final
            
            if historial.es_reporte_final:
                ingreso.estado = 'entregado'
                ingreso.save()
            return redirect('detalle_ingreso', numero_ingreso=numero_ingreso)
    else:
        form = InformeTecnicoForm()
    
    return render(request, 'gestion/reporte_final.html', {
        'ingreso': ingreso,
        'equipo': equipo,
        'cliente': cliente,
        'form': form,
    })

def generar_pdf_informe(request, numero_ingreso):
    ingreso = get_object_or_404(Ingreso, numero_ingreso=numero_ingreso)
    historial_final = HistorialEquipo.objects.filter(ingreso=ingreso, es_reporte_final=True).last()
    
    if not historial_final:
        return HttpResponse("No se encontró un informe técnico final para este ingreso", status=404)
    
    html_string = render_to_string('gestion/informe_pdf.html', {
        'ingreso': ingreso,
        'cliente': ingreso.equipo.cliente,
        'equipo': ingreso.equipo,
        'historial': historial_final,
    })
    
    pdf_file = HTML(string=html_string).write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=informe_ingreso_{numero_ingreso}.pdf'
    return response
    
def generar_pdf_ingreso(request, ingreso_id):
    from pathlib import Path
    ingreso = get_object_or_404(Ingreso, id=ingreso_id)
    equipo = ingreso.equipo
    cliente = equipo.cliente
    imagenes = ImagenIngreso.objects.filter(ingreso=ingreso)
    
    imagenes_rutas = []
    for img in ingreso.imagenes.all():
        ruta_absoluta = Path(settings.MEDIA_ROOT) / img.imagen.name
        ruta_uri = request.build_absolute_uri(img.imagen.url)  # file:///C:/...
        print(ruta_uri)
        imagenes_rutas.append({
                'ruta': ruta_uri,
                'descripcion': img.descripcion,
        })
    
    imagenes_serial = ImagenSerial.objects.filter(equipo=equipo)
    imagenes_serial_rutas = []
    for img in imagenes_serial:
        ruta_uri = request.build_absolute_uri(img.imagen.url)
        print(ruta_uri)
        imagenes_serial_rutas.append({
            'ruta': ruta_uri,
        })
       
    # Renderizar PDF desde template
    html = render_to_string('gestion/pdf_ingreso.html', {
        'ingreso': ingreso,
        'cliente': cliente,
        'equipo': equipo,
        'imagenes': imagenes_rutas,
        'imagenes_serial': imagenes_serial_rutas,
        
     })

     # Establecer base_url correctamente
    base_url = request.build_absolute_uri('/')

    pdf_file = HTML(string=html, base_url=base_url).write_pdf()

    # Respuesta con PDF descargable
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=ingreso_{ingreso.numero_ingreso}.pdf'
    return response

def ingreso_exitoso(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id)
    return render(request, 'gestion/ingreso_exitoso.html', {
        'ingreso': ingreso,
        'ingreso_id': ingreso_id
    })

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('inicio')
    
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'gestion/registro.html', {'form': form}) 

def login_personalizado(request):
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            if usuario.is_superuser:
                return redirect('/admin/')
            else:
                return redirect('inicio')
    else:
        form = AuthenticationForm()
    return render(request, 'gestion/login.html', {'form': form})

#Dashboard se renderiza en dashboard.html
def dashboard(request):
    """Dashboard principal con KPIs y gráficos"""
    
    # KPIs optimizados en una sola query
    stats = Ingreso.objects.aggregate(
        total=Count('id'),
        activos=Count('id', filter=~Q(estado='entregado')),
        entregados=Count('id', filter=Q(estado='entregado')),
        garantias=Count('id', filter=Q(es_garantia=True))
    )
    
    # Estados con etiquetas legibles
    estados_data = (
        Ingreso.objects.values('estado')
        .annotate(total=Count('id'))
        .order_by('-total')  # Ordenar por cantidad descendente
    )
    
    #Obtener lista de estados unicos para el filtro
    estados_disponibles = (
        Ingreso.objects
        .values_list('estado', flat=True)
        .distinct()
        .order_by('estado')
    )
    
    # Últimos 6 meses con nombres de mes
    hoy = now()
    hace_6_meses = hoy - timedelta(days=180)
    
    ingresos_mes = (
        Ingreso.objects
        .filter(fecha_ingreso__gte=hace_6_meses)
        .annotate(mes=TruncMonth('fecha_ingreso'))  # Más preciso que F('month')
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    
    # Formatear datos para el template
    ingresos_mes_formateados = [
        {
            'mes': item['mes'].strftime('%b %Y'),  # 'Ene 2024'
            'total': item['total']
        }
        for item in ingresos_mes
    ]
    
    context = {
        'total_ingresos': stats['total'],
        'activos': stats['activos'],
        'entregados': stats['entregados'],
        'garantias': stats['garantias'],
        'estados_data': list(estados_data),
        'ingresos_mes': ingresos_mes_formateados,
        'estadis_disponibles': list(estados_disponibles),
    }
    
    return render(request, 'gestion/dashboard.html', context)

#API devuelve estadisticas filtradas a Dashboard
@require_http_methods(["GET"])
def estadisticas_api(request):
    """API para estadísticas filtradas por fecha"""
    
    fecha_inicio = parse_date(request.GET.get('inicio', ''))
    fecha_fin = parse_date(request.GET.get('fin', ''))
    estado = request.GET.get('estado', '')
    
    # Validación de fechas
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        return JsonResponse({
            'error': 'La fecha de inicio no puede ser mayor que la fecha fin'
        }, status=400)
    
    #Construccion de filtros
    ingresos = Ingreso.objects.all()
    
    if fecha_inicio:
        ingresos = ingresos.filter(fecha_ingreso__date__gte=fecha_inicio)
    if fecha_fin:
        ingresos = ingresos.filter(fecha_ingreso__date__lte=fecha_fin)
    if estado:
        ingresos = ingresos.filter(estado=estado)
    
    # KPIs filtrados
    stats = ingresos.aggregate(
        total=Count('id'),
        activos=Count('id', filter=~Q(estado='entregado')),
        entregados=Count('id', filter=Q(estado='entregado')),
        garantias=Count('id', filter=Q(es_garantia=True))
    )
    
    # Estados
    estados_data = (
        ingresos.values('estado')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    
    # Ingresos por mes
    ingresos_mes = (
        ingresos
        .annotate(mes=TruncMonth('fecha_ingreso'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    
    ingresos_mes_formateados = [
        {
            'mes': item['mes'].strftime('%b %Y'),
            'total': item['total']
        }
        for item in ingresos_mes
    ]
    
    data = {
        'total_ingresos': stats['total'],
        'activos': stats['activos'],
        'entregados': stats['entregados'],
        'garantias': stats['garantias'],
        'estados': list(estados_data),
        'ingresos_mes': ingresos_mes_formateados,
    }
    
    return JsonResponse(data)