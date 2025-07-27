# crear_datos_prueba.py
# Ejecutar con: python manage.py shell < crear_datos_prueba.py

from socios.models import Plan, Socio, Pago
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# Crear planes
planes_data = [
    {'nombre': 'Plan 2 días', 'cant_dias_semana': 2, 'precio': 15000},
    {'nombre': 'Plan 3 días', 'cant_dias_semana': 3, 'precio': 20000},
    {'nombre': 'Pase Libre', 'cant_dias_semana': 5, 'precio': 30000},
]

print("Creando planes...")
for plan_data in planes_data:
    plan, created = Plan.objects.get_or_create(
        nombre=plan_data['nombre'],
        defaults=plan_data
    )
    if created:
        print(f"✅ Plan creado: {plan}")
    else:
        print(f"📋 Plan ya existe: {plan}")

# Crear socios de prueba
plan_2_dias = Plan.objects.get(nombre='Plan 2 días')
plan_3_dias = Plan.objects.get(nombre='Plan 3 días')
pase_libre = Plan.objects.get(nombre='Pase Libre')

socios_data = [
    {
        'nombre': 'Juan',
        'apellido': 'Pérez',
        'dni': '12345678',
        'email': 'juan.perez@email.com',
        'telefono': '351-1234567',
        'contacto_emergencia': '351-7654321',
        'plan': plan_3_dias,
        'codigo_acceso': '001',
        'fecha_inscripcion': date.today() - timedelta(days=30),
    },
    {
        'nombre': 'María',
        'apellido': 'González',
        'dni': '87654321',
        'email': 'maria.gonzalez@email.com',
        'telefono': '351-2345678',
        'contacto_emergencia': '351-8765432',
        'plan': pase_libre,
        'codigo_acceso': '002',
        'fecha_inscripcion': date.today() - timedelta(days=15),
    },
    {
        'nombre': 'Carlos',
        'apellido': 'López',
        'dni': '11223344',
        'email': 'carlos.lopez@email.com',
        'telefono': '351-3456789',
        'contacto_emergencia': '351-9876543',
        'plan': plan_2_dias,
        'codigo_acceso': '003',
        'fecha_inscripcion': date.today() - timedelta(days=60),
    }
]

print("\nCreando socios...")
for socio_data in socios_data:
    socio, created = Socio.objects.get_or_create(
        dni=socio_data['dni'],
        defaults=socio_data
    )
    if created:
        print(f"✅ Socio creado: {socio}")
    else:
        print(f"📋 Socio ya existe: {socio}")

# Crear pagos (algunos al día, otros vencidos)
print("\nCreando pagos...")

# Juan - al día (pagó este mes)
juan = Socio.objects.get(dni='12345678')
pago_juan, created = Pago.objects.get_or_create(
    socio=juan,
    mes_correspondiente=date.today().replace(day=1),
    defaults={
        'monto': juan.plan.precio,
        'metodo_pago': 'efectivo'
    }
)
if created:
    print(f"✅ Pago creado para Juan: {pago_juan}")

# María - al día (pagó este mes)
maria = Socio.objects.get(dni='87654321')
pago_maria, created = Pago.objects.get_or_create(
    socio=maria,
    mes_correspondiente=date.today().replace(day=1),
    defaults={
        'monto': maria.plan.precio,
        'metodo_pago': 'transferencia'
    }
)
if created:
    print(f"✅ Pago creado para María: {pago_maria}")

# Carlos - vencido (pagó el mes pasado)
carlos = Socio.objects.get(dni='11223344')
mes_pasado = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
pago_carlos, created = Pago.objects.get_or_create(
    socio=carlos,
    mes_correspondiente=mes_pasado,
    defaults={
        'monto': carlos.plan.precio,
        'metodo_pago': 'efectivo'
    }
)
if created:
    print(f"✅ Pago creado para Carlos (mes pasado): {pago_carlos}")

print("\n🎉 Datos de prueba creados exitosamente!")
print("\n📊 Resumen:")
print(f"- Planes: {Plan.objects.count()}")
print(f"- Socios: {Socio.objects.count()}")
print(f"- Pagos: {Pago.objects.count()}")

print("\n🧪 Para probar:")
print("1. Juan y María están al día (pueden fichar)")
print("2. Carlos está vencido (no puede fichar)")
print("3. Códigos para probar:")
print("   - Juan: 001")
print("   - María: 002") 
print("   - Carlos: 003")