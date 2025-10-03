from django.db import models
from django.contrib.auth.models import User

class Reporte(models.Model):
    """Modelo para reportes del sistema"""
    tipo = models.CharField(max_length=50, choices=[
        ('ASISTENCIA', 'Reporte de Asistencia'),
        ('PAGOS', 'Reporte de Pagos'),
        ('USUARIOS', 'Reporte de Usuarios'),
        ('AUDITORIA', 'Reporte de Auditoría')
    ])
    parametros = models.JSONField(default=dict)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes')
    archivo = models.FileField(upload_to='reportes/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('GENERANDO', 'Generando'),
        ('COMPLETADO', 'Completado'),
        ('ERROR', 'Error')
    ], default='GENERANDO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reportes_reporte'

    def __str__(self):
        return f"Reporte {self.tipo} - {self.autor.username}"
