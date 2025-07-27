from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Sum, Count, Q
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import json

from .models import Socio, Ingreso, Pago, Plan

# ========== SISTEMA DE FICHAJE ==========

@csrf_exempt
@require_http_methods(["POST"])
def fichar(request, codigo_acceso):
    """Endpoint para el fichaje con código de acceso"""
    try:
        socio = get_object_or_404(Socio, codigo_acceso=codigo_acceso)
        
        puede_ingresar, mensaje = socio.puede_ingresar()
        
        if not puede_ingresar:
            return JsonResponse({
                'estado': 'denegado',
                'mensaje': f"{socio.nombre}, {mensaje}",
                'socio': socio.nombre,
                'plan': socio.plan.nombre,
                'fecha_vencimiento': socio.fecha_vencimiento_actual.strftime('%d/%m/%Y') if socio.fecha_vencimiento_actual else 'Sin pagos'
            })
        
        # Registrar ingreso
        Ingreso.objects.create(socio=socio)
        
        # Calcular información para mostrar
        dias_usados_semana = socio.ingresos_semana_actual()
        dias_restantes_semana = socio.plan.cant_dias_semana - dias_usados_semana
        
        return JsonResponse({
            'estado': 'aprobado',
            'mensaje': f"¡Bienvenido {socio.nombre}!",
            'socio': f"{socio.nombre} {socio.apellido}",
            'plan': socio.plan.nombre,
            'dias_restantes_semana': dias_restantes_semana,
            'fecha_vencimiento': socio.fecha_vencimiento_actual.strftime('%d/%m/%Y'),
            'dias_hasta_vencimiento': socio.dias_hasta_vencimiento
        })
        
    except Socio.DoesNotExist:
        return JsonResponse({
            'estado': 'error',
            'mensaje': 'Código no reconocido'
        })
    except Exception as e:
        return JsonResponse({
            'estado': 'error',
            'mensaje': f'Error del sistema: {str(e)}'
        })

@require_http_methods(["GET"])
def consultar_socio(request, codigo_acceso):
    """Consultar estado de un socio sin registrar ingreso"""
    try:
        socio = get_object_or_404(Socio, codigo_acceso=codigo_acceso)
        
        return JsonResponse({
            'estado': 'ok',
            'socio': f"{socio.nombre} {socio.apellido}",
            'plan': socio.plan.nombre,
            'esta_al_dia': socio.esta_al_dia,
            'fecha_vencimiento': socio.fecha_vencimiento_actual.strftime('%d/%m/%Y') if socio.fecha_vencimiento_actual else 'Sin pagos',
            'dias_hasta_vencimiento': socio.dias_hasta_vencimiento,
            'ingresos_semana': socio.ingresos_semana_actual(),
            'limite_semanal': socio.plan.cant_dias_semana,
            'puede_ingresar': socio.puede_ingresar()[0]
        })
        
    except Socio.DoesNotExist:
        return JsonResponse({
            'estado': 'error',
            'mensaje': 'Socio no encontrado'
        })

# ========== PANEL ADMINISTRATIVO ==========

def dashboard(request):
    """Panel principal con estadísticas"""
    hoy = date.today()
    
    # Estadísticas generales
    total_socios = Socio.objects.count()
    socios_activos = Socio.objects.filter(activo=True)
    socios_al_dia = sum(1 for s in socios_activos if s.esta_al_dia)
    
    # Recaudación del mes
    recaudacion_mes = Pago.objects.filter(
        fecha_pago__month=hoy.month,
        fecha_pago__year=hoy.year
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    # Actividad reciente
    ultimos_ingresos = Ingreso.objects.select_related('socio', 'socio__plan').order_by('-fecha')[:5]
    ultimos_pagos = Pago.objects.select_related('socio').order_by('-fecha_pago')[:5]
    
    # Socios con vencimiento próximo (7 días)
    socios_vencimiento_proximo = [
        socio for socio in socios_activos 
        if socio.esta_al_dia and 0 <= socio.dias_hasta_vencimiento <= 7
    ]
    
    # Datos para gráficos - Ingresos últimos 7 días
    labels_ingresos = []
    datos_ingresos = []
    for i in range(7):
        fecha = hoy - timedelta(days=6-i)
        labels_ingresos.append(fecha.strftime('%d/%m'))
        count = Ingreso.objects.filter(fecha__date=fecha).count()
        datos_ingresos.append(count)
    
    # Datos para gráfico de planes
    distribucion_planes = Plan.objects.annotate(
        total=Count('socio', filter=Q(socio__activo=True))
    ).values('nombre', 'total')
    
    labels_planes = [plan['nombre'] for plan in distribucion_planes]
    datos_planes = [plan['total'] for plan in distribucion_planes]
    
    context = {
        'total_socios': total_socios,
        'socios_al_dia': socios_al_dia,
        'socios_vencidos': len(socios_activos) - socios_al_dia,
        'recaudacion_mes': recaudacion_mes,
        'mes_actual': hoy.strftime('%B %Y'),
        'ultimos_ingresos': ultimos_ingresos,
        'ultimos_pagos': ultimos_pagos,
        'socios_vencimiento_proximo': socios_vencimiento_proximo,
        'labels_ingresos': json.dumps(labels_ingresos),
        'datos_ingresos': json.dumps(datos_ingresos),
        'labels_planes': json.dumps(labels_planes),
        'datos_planes': json.dumps(datos_planes),
    }
    
    return render(request, 'socios/dashboard.html', context)

def lista_socios(request):
    """Lista de todos los socios con filtros"""
    estado = request.GET.get('estado', 'todos')
    
    socios = Socio.objects.all().order_by('apellido', 'nombre')
    
    if estado == 'activos':
        socios = [s for s in socios if s.esta_al_dia]
    elif estado == 'vencidos':
        socios = [s for s in socios if s.activo and not s.esta_al_dia]
    elif estado == 'inactivos':
        socios = socios.filter(activo=False)
    
    context = {
        'socios': socios,
        'estado_filtro': estado
    }
    
    return render(request, 'socios/lista_socios.html', context)

def lista_ingresos(request):
    """Lista de ingresos con filtros"""
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    ingresos = Ingreso.objects.select_related('socio', 'socio__plan').order_by('-fecha')
    
    if fecha_desde:
        ingresos = ingresos.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        ingresos = ingresos.filter(fecha__date__lte=fecha_hasta)
    
    # Paginación simple - últimos 50
    ingresos = ingresos[:50]
    
    context = {
        'ingresos': ingresos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta
    }
    
    return render(request, 'socios/lista_ingresos.html', context)

def lista_pagos(request):
    """Lista de pagos con filtros"""
    mes = request.GET.get('mes')
    año = request.GET.get('año', date.today().year)
    
    pagos = Pago.objects.select_related('socio').order_by('-fecha_pago')
    
    if mes:
        pagos = pagos.filter(fecha_pago__month=mes, fecha_pago__year=año)
    
    # Paginación simple - últimos 50
    pagos = pagos[:50]
    
    context = {
        'pagos': pagos,
        'mes': mes,
        'año': año
    }
    
    return render(request, 'socios/lista_pagos.html', context)

def registrar_socio(request):
    """Registrar nuevo socio"""
    if request.method == 'POST':
        try:
            socio = Socio.objects.create(
                nombre=request.POST['nombre'],
                apellido=request.POST['apellido'],
                dni=request.POST['dni'],
                email=request.POST['email'],
                telefono=request.POST.get('telefono', ''),
                contacto_emergencia=request.POST['contacto_emergencia'],
                plan_id=request.POST['plan'],
                codigo_acceso=request.POST['codigo_acceso'],
                fecha_inscripcion=request.POST['fecha_inscripcion'],
                observaciones=request.POST.get('observaciones', '')
            )
            messages.success(request, f'Socio {socio} registrado exitosamente')
            return redirect('lista_socios')
        except Exception as e:
            messages.error(request, f'Error al registrar socio: {str(e)}')
    
    planes = Plan.objects.all()
    return render(request, 'socios/registrar_socio.html', {'planes': planes})

def registrar_pago_form(request):
    """Formulario para registrar pagos"""
    socios = Socio.objects.filter(activo=True).order_by('apellido', 'nombre')
    planes = Plan.objects.all().order_by('cant_dias_semana')
    
    # Preparar datos de socios para JavaScript
    socios_data = []
    for socio in socios:
        socios_data.append({
            'id': socio.id,
            'nombre': socio.nombre,
            'apellido': socio.apellido,
            'dni': socio.dni,
            'email': socio.email,
            'plan': socio.plan.nombre,
            'plan_id': socio.plan.id,
            'precio': float(socio.plan.precio),
            'esta_al_dia': socio.esta_al_dia,
            'fecha_vencimiento': socio.fecha_vencimiento_actual.strftime('%d/%m/%Y') if socio.fecha_vencimiento_actual else 'Sin pagos',
            'estado_texto': socio.estado_texto
        })
    
    # Preparar datos de planes para JavaScript
    planes_data = []
    for plan in planes:
        planes_data.append({
            'id': plan.id,
            'nombre': plan.nombre,
            'precio': float(plan.precio),
            'cant_dias_semana': plan.cant_dias_semana
        })
    
    context = {
        'socios': socios,
        'planes': planes,
        'socios_json': json.dumps(socios_data),
        'planes_json': json.dumps(planes_data)
    }
    return render(request, 'socios/registrar_pago.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def registrar_pago(request):
    """Registrar pago de membresía - PERMITE RENOVACIONES SIEMPRE"""
    try:
        data = json.loads(request.body)
        
        # Obtener el socio
        socio = get_object_or_404(Socio, id=data['socio_id'])
        plan_nuevo_id = data.get('plan_nuevo_id')
        
        # Convertir strings de fecha a objetos date
        fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        fecha_vencimiento = datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%d').date()
        
        # Validar que vencimiento sea posterior a inicio
        if fecha_vencimiento <= fecha_inicio:
            return JsonResponse({
                'estado': 'error',
                'mensaje': 'La fecha de vencimiento debe ser posterior a la fecha de inicio'
            })
        
        # Verificar si hay cambio de plan
        cambio_plan = False
        plan_anterior = socio.plan.nombre
        if plan_nuevo_id and int(plan_nuevo_id) != socio.plan.id:
            plan_nuevo = get_object_or_404(Plan, id=plan_nuevo_id)
            socio.plan = plan_nuevo
            socio.save()
            cambio_plan = True
        
        # Crear el pago - SIN RESTRICCIONES DE ESTADO
        pago = Pago.objects.create(
            socio=socio,
            fecha_inicio_periodo=fecha_inicio,
            fecha_vencimiento_periodo=fecha_vencimiento,
            monto=data['monto'],
            metodo_pago=data['metodo_pago'],
            comprobante=data.get('comprobante', '')
        )
        
        # Calcular días del período
        dias_periodo = (fecha_vencimiento - fecha_inicio).days
        
        # Crear mensaje informativo
        mensaje = f'Pago registrado para {socio.nombre} {socio.apellido}'
        if cambio_plan:
            mensaje += f'. Plan actualizado de "{plan_anterior}" a "{socio.plan.nombre}"'
        
        if dias_periodo != 30:
            mensaje += f'. Período: {dias_periodo} días'
        
        return JsonResponse({
            'estado': 'ok',
            'mensaje': mensaje,
            'pago_id': pago.id,
            'cambio_plan': cambio_plan,
            'plan_nuevo': socio.plan.nombre if cambio_plan else None,
            'periodo_dias': dias_periodo,
            'es_periodo_estandar': dias_periodo == 30,
            'fecha_inicio': fecha_inicio.strftime('%d/%m/%Y'),
            'fecha_vencimiento': fecha_vencimiento.strftime('%d/%m/%Y')
        })
        
    except ValueError as e:
        return JsonResponse({
            'estado': 'error',
            'mensaje': f'Error en formato de fechas: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({
            'estado': 'error',
            'mensaje': f'Error al registrar pago: {str(e)}'
        })

def reporte_recaudacion(request):
    """Reporte de recaudación mensual"""
    año = int(request.GET.get('año', date.today().year))
    mes = int(request.GET.get('mes', date.today().month))
    
    # Pagos del mes
    pagos = Pago.objects.filter(
        fecha_pago__year=año,
        fecha_pago__month=mes
    ).order_by('-fecha_pago')
    
    # Totales por método de pago
    totales_metodo = Pago.objects.filter(
        fecha_pago__year=año,
        fecha_pago__month=mes
    ).values('metodo_pago').annotate(total=Sum('monto'))
    
    total_mes = sum(item['total'] for item in totales_metodo)
    
    context = {
        'pagos': pagos,
        'totales_metodo': totales_metodo,
        'total_mes': total_mes,
        'año': año,
        'mes': mes,
        'nombre_mes': date(año, mes, 1).strftime('%B %Y')
    }
    
    return render(request, 'socios/reporte_recaudacion.html', context)

# ========== KIOSCO DE FICHAJE ==========

def kiosco_fichaje(request):
    """Pantalla principal del kiosco para fichaje de socios"""
    return render(request, 'socios/kiosco_fichaje.html')

@csrf_exempt
@require_http_methods(["POST"])
def fichar_dni(request):
    """Fichaje usando DNI"""
    try:
        data = json.loads(request.body)
        dni = data.get('dni', '').strip()
        
        if not dni:
            return JsonResponse({
                'estado': 'error',
                'mensaje': 'Ingresa tu DNI',
                'tipo': 'warning'
            })
        
        # Buscar socio por DNI
        try:
            socio = Socio.objects.get(dni=dni, activo=True)
        except Socio.DoesNotExist:
            return JsonResponse({
                'estado': 'error',
                'mensaje': 'DNI no encontrado o socio inactivo',
                'tipo': 'danger'
            })
        
        # Verificar si puede ingresar
        puede_ingresar, mensaje = socio.puede_ingresar()
        
        if not puede_ingresar:
            return JsonResponse({
                'estado': 'denegado',
                'mensaje': mensaje,
                'socio': f"{socio.nombre} {socio.apellido}",
                'plan': socio.plan.nombre,
                'fecha_vencimiento': socio.fecha_vencimiento_actual.strftime('%d/%m/%Y') if socio.fecha_vencimiento_actual else 'Sin pagos',
                'tipo': 'danger'
            })
        
        # Registrar ingreso exitoso
        Ingreso.objects.create(socio=socio)
        
        # Calcular información para mostrar
        dias_usados_semana = socio.ingresos_semana_actual()
        dias_restantes_semana = socio.plan.cant_dias_semana - dias_usados_semana
        
        return JsonResponse({
            'estado': 'aprobado',
            'mensaje': 'Acceso permitido',
            'socio': f"{socio.nombre} {socio.apellido}",
            'plan': socio.plan.nombre,
            'dias_restantes_semana': dias_restantes_semana,
            'dias_totales_semana': socio.plan.cant_dias_semana,
            'fecha_vencimiento': socio.fecha_vencimiento_actual.strftime('%d/%m/%Y'),
            'dias_hasta_vencimiento': socio.dias_hasta_vencimiento,
            'tipo': 'success'
        })
        
    except Exception as e:
        return JsonResponse({
            'estado': 'error',
            'mensaje': f'Error del sistema: {str(e)}',
            'tipo': 'danger'
        })