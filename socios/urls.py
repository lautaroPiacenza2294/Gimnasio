from django.urls import path
from .views import fichar, registrar_pago

urlpatterns = [
    path('fichar/<str:huella_id>/', fichar, name='fichar'),
    path('registrar-pago/', registrar_pago, name='registrar_pago'),
]

