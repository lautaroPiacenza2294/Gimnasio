from django.db import models

# Create your models here.

class Plan(models.Model):
    nombre = models.CharField(max_length=50, blank=True)  
    cant_dias = models.IntegerField()
    precio = models.CharField(max_length=15)

    def __str__(self):
        return self.nombre


class Socio(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=10, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    contacto_emergencia = models.CharField(max_length=100, help_text="Teléfono de un familiar o persona de contacto")
    plan_id = models.ForeignKey(Plan, on_delete=models.CASCADE)
    huella_id = models.CharField(max_length=100, unique=True)
    fecha_inicio = models.DateField()
    estado = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Ingreso(models.Model):
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ingreso de {self.socio} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

class Pago(models.Model):
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    fecha_pago = models.DateField(auto_now_add=True)
    mes_correspondiente = models.DateField()
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, choices=[
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('otro', 'Otro'),
    ])

    def __str__(self):
        return f"Pago de {self.socio} - {self.mes_correspondiente.strftime('%B %Y')}"
