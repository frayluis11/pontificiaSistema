# Admin básico para el microservicio de pagos
from django.contrib import admin
from .models import Pago, Planilla, Boleta, Adelanto, Descuento, Bonificacion

# Registro básico de modelos
admin.site.register(Pago)
admin.site.register(Planilla)
admin.site.register(Boleta)
admin.site.register(Adelanto)
admin.site.register(Descuento)
admin.site.register(Bonificacion)