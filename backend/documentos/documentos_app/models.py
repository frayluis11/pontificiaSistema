from django.db import models
from django.contrib.auth.models import User

class Documento(models.Model):
    """Modelo principal para documentos"""
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, choices=[
        ('CONTRATO', 'Contrato'),
        ('ACTA', 'Acta'),
        ('RESOLUCION', 'Resolución'),
        ('MEMO', 'Memorando'),
        ('CARTA', 'Carta')
    ])
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')
    estado = models.CharField(max_length=20, choices=[
        ('BORRADOR', 'Borrador'),
        ('REVISION', 'En Revisión'),
        ('APROBADO', 'Aprobado'),
        ('FIRMADO', 'Firmado'),
        ('RECHAZADO', 'Rechazado')
    ], default='BORRADOR')
    archivo = models.FileField(upload_to='documentos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documentos_documento'

    def __str__(self):
        return f"{self.titulo} - {self.tipo}"
