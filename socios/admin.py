from django.contrib import admin

# Register your models here.

from .models import Socio, Ingreso, Pago

admin.site.register(Socio)
admin.site.register(Ingreso)
admin.site.register(Pago)
