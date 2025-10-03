from django.db import models
from django.contrib.auth.models import User

class RegistroHora(models.Model):
    """Modelo para registrar asistencia de docentes"""
    docente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_hora')
    aula = models.CharField(max_length=50)
    seccion = models.CharField(max_length=50)
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('PUNTUAL', 'Puntual'),
        ('TARDANZA', 'Tardanza'),
        ('AUSENTE', 'Ausente'),
        ('JUSTIFICADO', 'Justificado')
    ], default='PUNTUAL')
    observacion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asistencia_registro_hora'
        unique_together = ['docente', 'fecha', 'seccion']

    def __str__(self):
        return f"{self.docente.username} - {self.fecha} - {self.seccion}"

class JustificacionAusencia(models.Model):
    """Modelo para justificar ausencias"""
    docente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='justificaciones')
    fecha = models.DateField()
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=[
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado')
    ], default='PENDIENTE')
    archivo_adjunto = models.FileField(upload_to='justificaciones/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asistencia_justificacion'

    def __str__(self):
        return f"Justificación {self.docente.username} - {self.fecha}"
