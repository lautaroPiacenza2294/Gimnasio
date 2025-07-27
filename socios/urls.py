from django.urls import path
from .views import (
    fichar, registrar_pago, consultar_socio, dashboard, 
    lista_socios, lista_ingresos, lista_pagos, registrar_socio, 
    reporte_recaudacion, registrar_pago_form, kiosco_fichaje, fichar_dni
)

urlpatterns = [
    # Panel administrativo
    path('', dashboard, name='dashboard'),
    path('socios/', lista_socios, name='lista_socios'),
    path('socios/nuevo/', registrar_socio, name='registrar_socio'),
    path('ingresos/', lista_ingresos, name='lista_ingresos'),
    path('pagos/', lista_pagos, name='lista_pagos'),
    path('pagos/nuevo/', registrar_pago_form, name='registrar_pago_form'),
    path('reportes/', reporte_recaudacion, name='reporte_recaudacion'),
    
    # NUEVO: Kiosco de fichaje
    path('kiosco/', kiosco_fichaje, name='kiosco_fichaje'),
    path('fichar-dni/', fichar_dni, name='fichar_dni'),
    
    # API para fichaje
    path('fichar/<str:codigo_acceso>/', fichar, name='fichar'),
    path('consultar/<str:codigo_acceso>/', consultar_socio, name='consultar_socio'),
    path('registrar-pago/', registrar_pago, name='registrar_pago'),
]