"""
Modelos para el sistema de asistencia
Sistema Pontificia - Asistencia Service
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime, time, timedelta


class RegistroHora(models.Model):
    """
    Modelo para registrar asistencia de docentes
    """
    ESTADO_CHOICES = [
        ('PUNTUAL', 'Puntual'),
        ('TARDANZA', 'Tardanza'),
        ('AUSENTE', 'Ausente'),
        ('JUSTIFICADO', 'Justificado'),
        ('FALTA', 'Falta')
    ]
    
    docente_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='ID del docente desde el servicio AUTH'
    )
    aula = models.CharField(max_length=50, help_text='Aula donde se dicta la clase')
    seccion = models.CharField(max_length=50, help_text='Sección o grupo de estudiantes')
    fecha = models.DateField(help_text='Fecha del registro de asistencia')
    hora_entrada = models.TimeField(help_text='Hora de entrada registrada')
    hora_salida = models.TimeField(
        null=True, 
        blank=True, 
        help_text='Hora de salida (opcional)'
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='PUNTUAL',
        help_text='Estado de la asistencia'
    )
    observacion = models.TextField(
        blank=True, 
        help_text='Observaciones adicionales'
    )
    minutos_tardanza = models.PositiveIntegerField(
        default=0,
        help_text='Minutos de tardanza calculados'
    )
    descuento_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Descuento monetario aplicado por tardanza'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'registro_asistencia'
        unique_together = ['docente_id', 'fecha', 'seccion']
        indexes = [
            models.Index(fields=['docente_id'], name='idx_docente_id'),
            models.Index(fields=['fecha'], name='idx_fecha'),
            models.Index(fields=['estado'], name='idx_estado'),
            models.Index(fields=['fecha_creacion'], name='idx_fecha_creacion'),
        ]
        ordering = ['-fecha', '-hora_entrada']

    def __str__(self):
        return f"Docente {self.docente_id} - {self.fecha} - {self.seccion} ({self.estado})"
    
    @property
    def es_tardanza(self):
        """Determina si el registro es una tardanza basado en los minutos"""
        return self.minutos_tardanza > 5  # 5 minutos de tolerancia
    
    @property
    def horas_trabajadas(self):
        """Calcula las horas trabajadas si hay hora de salida"""
        if self.hora_salida and self.hora_entrada:
            entrada = datetime.combine(self.fecha, self.hora_entrada)
            salida = datetime.combine(self.fecha, self.hora_salida)
            if salida > entrada:
                delta = salida - entrada
                return delta.total_seconds() / 3600
        return None
    
    def save(self, *args, **kwargs):
        """Override save para calcular automáticamente el estado y tardanza"""
        if self.minutos_tardanza > 5:
            self.estado = 'TARDANZA'
        elif self.minutos_tardanza <= 5 and self.estado not in ['AUSENTE', 'FALTA', 'JUSTIFICADO']:
            self.estado = 'PUNTUAL'
        
        super().save(*args, **kwargs)

class JustificacionAusencia(models.Model):
    """
    Modelo para justificar ausencias de docentes
    """
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de revisión'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('EN_REVISION', 'En revisión')
    ]
    
    TIPO_MOTIVO_CHOICES = [
        ('ENFERMEDAD', 'Enfermedad'),
        ('EMERGENCIA_FAMILIAR', 'Emergencia familiar'),
        ('PERMISO_PERSONAL', 'Permiso personal'),
        ('CAPACITACION', 'Capacitación'),
        ('OTROS', 'Otros')
    ]
    
    docente_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='ID del docente desde el servicio AUTH'
    )
    fecha = models.DateField(help_text='Fecha de la ausencia a justificar')
    motivo = models.TextField(help_text='Motivo detallado de la ausencia')
    tipo_motivo = models.CharField(
        max_length=50,
        choices=TIPO_MOTIVO_CHOICES,
        default='OTROS',
        help_text='Categoría del motivo'
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='PENDIENTE',
        help_text='Estado de la justificación'
    )
    archivo_adjunto = models.FileField(
        upload_to='justificaciones/', 
        null=True, 
        blank=True,
        help_text='Documento de respaldo (opcional)'
    )
    observaciones_revisor = models.TextField(
        blank=True,
        help_text='Observaciones del revisor'
    )
    fecha_revision = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de revisión de la justificación'
    )
    revisor_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID del usuario que revisó la justificación'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'justificacion_ausencia'
        indexes = [
            models.Index(fields=['docente_id'], name='idx_just_docente_id'),
            models.Index(fields=['fecha'], name='idx_just_fecha'),
            models.Index(fields=['estado'], name='idx_just_estado'),
            models.Index(fields=['fecha_creacion'], name='idx_just_fecha_creacion'),
        ]
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Justificación Docente {self.docente_id} - {self.fecha} ({self.get_estado_display()})"
    
    @property
    def dias_desde_solicitud(self):
        """Calcula los días transcurridos desde la solicitud"""
        return (timezone.now().date() - self.fecha_creacion.date()).days
    
    @property
    def es_urgente(self):
        """Determina si la justificación es urgente (más de 3 días sin revisar)"""
        return self.estado == 'PENDIENTE' and self.dias_desde_solicitud > 3
    
    def aprobar(self, revisor_id, observaciones=''):
        """Aprueba la justificación"""
        self.estado = 'APROBADO'
        self.revisor_id = revisor_id
        self.observaciones_revisor = observaciones
        self.fecha_revision = timezone.now()
        self.save()
    
    def rechazar(self, revisor_id, observaciones):
        """Rechaza la justificación"""
        self.estado = 'RECHAZADO'
        self.revisor_id = revisor_id
        self.observaciones_revisor = observaciones
        self.fecha_revision = timezone.now()
        self.save()
