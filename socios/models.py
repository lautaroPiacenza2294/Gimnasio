from django.db import models
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class Plan(models.Model):
    nombre = models.CharField(max_length=50)  
    cant_dias_semana = models.IntegerField(help_text="Días permitidos por semana (2, 3 o 5)")
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.cant_dias_semana} días/semana"

class Socio(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=10, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    contacto_emergencia = models.CharField(max_length=100, help_text="Teléfono de un familiar o persona de contacto")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    codigo_acceso = models.CharField(max_length=20, unique=True, help_text="Código de acceso del socio")
    fecha_inscripcion = models.DateField()
    observaciones = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True, help_text="Estado administrativo del socio")
    
    # NUEVO: Campos para huella dactilar
    huella_template = models.TextField(blank=True, null=True, help_text="Template de huella dactilar codificado")
    huella_registrada = models.BooleanField(default=False, help_text="Si tiene huella registrada")

    
    @property
    def ultimo_pago(self):
        """Obtiene el último pago realizado basado en la fecha de pago más reciente"""
        return self.pago_set.order_by('-fecha_pago').first()

    @property
    def fecha_vencimiento_actual(self):
        """Fecha de vencimiento basada en el último pago registrado"""
        ultimo_pago = self.ultimo_pago
        if ultimo_pago:
            return ultimo_pago.fecha_vencimiento_periodo
        return None

    @property
    def esta_al_dia(self):
        """Verifica si el socio está al día con los pagos"""
        if not self.activo:
            return False
            
        fecha_vencimiento = self.fecha_vencimiento_actual
        if not fecha_vencimiento:
            return False
            
        return date.today() <= fecha_vencimiento

    @property
    def dias_hasta_vencimiento(self):
        """Días hasta que venza la membresía"""
        fecha_vencimiento = self.fecha_vencimiento_actual
        if fecha_vencimiento:
            return (fecha_vencimiento - date.today()).days
        return 0

    @property
    def dias_vencido_texto(self):
        """Texto descriptivo del estado de vencimiento"""
        if not self.fecha_vencimiento_actual:
            return "Sin pagos"
        
        dias = self.dias_hasta_vencimiento
        if dias > 0:
            return f"{dias} días restantes"
        elif dias == 0:
            return "Vence hoy"
        else:
            return f"Vencido hace {abs(dias)} días"

    @property
    def estado_badge_class(self):
        """Clase CSS para el badge de estado"""
        if not self.activo:
            return "bg-danger"
        elif self.esta_al_dia:
            if self.dias_hasta_vencimiento <= 7:
                return "bg-warning"
            return "bg-success"
        else:
            return "bg-danger"

    @property
    def estado_texto(self):
        """Texto del estado del socio"""
        if not self.activo:
            return "Inactivo"
        elif self.esta_al_dia:
            if self.dias_hasta_vencimiento <= 7:
                return "Próximo a vencer"
            return "Al día"
        else:
            return "Vencido"

    def ingresos_semana_actual(self):
        """Cuenta los ingresos de la semana actual"""
        hoy = date.today()
        lunes = hoy - timedelta(days=hoy.weekday())
        return Ingreso.objects.filter(socio=self, fecha__date__gte=lunes).count()

    def puede_ingresar(self):
        """Verifica si el socio puede ingresar hoy"""
        if not self.esta_al_dia:
            return False, "Membresía vencida"
            
        if self.ingresos_semana_actual() >= self.plan.cant_dias_semana:
            return False, f"Ya usaste los {self.plan.cant_dias_semana} días permitidos esta semana"
            
        if Ingreso.objects.filter(socio=self, fecha__date=date.today()).exists():
            return False, "Ya registraste un ingreso hoy"
            
        return True, "Puede ingresar"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Ingreso(models.Model):
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Ingreso de {self.socio} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

class Pago(models.Model):
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('otro', 'Otro'),
    ]
    
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    fecha_pago = models.DateField(auto_now_add=True, help_text="Cuándo se registró el pago")
    fecha_inicio_periodo = models.DateField(help_text="Cuándo inicia el período pagado")
    fecha_vencimiento_periodo = models.DateField(help_text="Cuándo vence el período pagado")
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, choices=METODOS_PAGO)
    comprobante = models.CharField(max_length=100, blank=True, null=True)
    
    # Campo para compatibilidad con datos existentes (opcional)
    mes_correspondiente = models.DateField(blank=True, null=True, help_text="Campo legacy - usar fecha_inicio_periodo")

    class Meta:
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de {self.socio} - {self.fecha_inicio_periodo.strftime('%d/%m/%Y')} a {self.fecha_vencimiento_periodo.strftime('%d/%m/%Y')}"

    @property
    def dias_periodo(self):
        """Cantidad de días del período pagado"""
        return (self.fecha_vencimiento_periodo - self.fecha_inicio_periodo).days

    @property
    def es_periodo_estandar(self):
        """Verifica si es un período estándar de 30 días"""
        return self.dias_periodo == 30