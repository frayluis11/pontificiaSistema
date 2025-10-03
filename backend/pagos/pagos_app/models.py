from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Pago(models.Model):
    """Modelo principal para pagos de trabajadores"""
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagos')
    periodo = models.CharField(max_length=7)  # 2025-01
    monto_bruto = models.DecimalField(max_digits=10, decimal_places=2)
    descuentos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    bonificaciones = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=[
        ('CALCULADO', 'Calculado'),
        ('PAGADO', 'Pagado'),
        ('ANULADO', 'Anulado')
    ], default='CALCULADO')
    fecha_pago = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pagos_pago'
        unique_together = ['trabajador', 'periodo']

    def __str__(self):
        return f"Pago {self.trabajador.username} - {self.periodo}"
