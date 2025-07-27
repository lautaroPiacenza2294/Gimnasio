from django.contrib import admin
from .models import Plan, Socio, Ingreso, Pago

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cant_dias_semana', 'precio']
    list_filter = ['cant_dias_semana']

@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'dni', 'plan', 'activo']
    list_filter = ['plan', 'activo', 'fecha_inscripcion']
    search_fields = ['nombre', 'apellido', 'dni', 'email']

@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ['socio', 'fecha']
    list_filter = ['fecha']
    search_fields = ['socio__nombre', 'socio__apellido']

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['socio', 'mes_correspondiente', 'monto', 'metodo_pago', 'fecha_pago']
    list_filter = ['metodo_pago', 'fecha_pago']
    search_fields = ['socio__nombre', 'socio__apellido']