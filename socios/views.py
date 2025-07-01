def fichar(request, huella_id):
    socio = get_object_or_404(Socio, huella_id=huella_id)

    # Verificamos si tiene la membresía activa
    if date.today() > socio.fecha_vencimiento:
        return JsonResponse({
            'estado': 'vencido',
            'mensaje': f"{socio.nombre}, tu membresía está vencida desde el {socio.fecha_vencimiento}."
        })

    # Filtramos ingresos de esta semana
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    ingresos_semana = Ingreso.objects.filter(socio=socio, fecha__date__gte=lunes)

    # Obtener límite desde el modelo Plan
    limite = socio.plan.cant_dias

    if ingresos_semana.count() >= limite:
        return JsonResponse({
            'estado': 'excedido',
            'mensaje': f"{socio.nombre}, ya usaste los {limite} días permitidos esta semana."
        })

    # Registrar ingreso
    Ingreso.objects.create(socio=socio)

    dias_restantes = limite - ingresos_semana.count() - 1  # -1 por el ingreso actual

    return JsonResponse({
        'estado': 'ok',
        'mensaje': f"{socio.nombre}, ingreso registrado. Te quedan {dias_restantes} días esta semana."
    })
