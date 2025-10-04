from django.db import models
from django.contrib.auth.models import User


class EstadoDocumento:
    """Estados posibles de un documento"""
    BORRADOR = 'BORRADOR'
    EN_REVISION = 'REVISION'
    APROBADO = 'APROBADO'
    FIRMADO = 'FIRMADO'
    RECHAZADO = 'RECHAZADO'
    ARCHIVADO = 'ARCHIVADO'
    
    CHOICES = [
        (BORRADOR, 'Borrador'),
        (EN_REVISION, 'En Revisión'),
        (APROBADO, 'Aprobado'),
        (FIRMADO, 'Firmado'),
        (RECHAZADO, 'Rechazado'),
        (ARCHIVADO, 'Archivado'),
    ]


class TipoDocumento:
    """Tipos de documentos"""
    CONTRATO = 'CONTRATO'
    ACTA = 'ACTA'
    RESOLUCION = 'RESOLUCION'
    MEMO = 'MEMO'
    CARTA = 'CARTA'
    
    CHOICES = [
        (CONTRATO, 'Contrato'),
        (ACTA, 'Acta'),
        (RESOLUCION, 'Resolución'),
        (MEMO, 'Memorando'),
        (CARTA, 'Carta'),
    ]


class EstadoSolicitud:
    """Estados de solicitudes"""
    PENDIENTE = 'PENDIENTE'
    EN_PROCESO = 'EN_PROCESO'
    APROBADO = 'APROBADO'
    RECHAZADO = 'RECHAZADO'
    COMPLETADO = 'COMPLETADO'
    
    CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (EN_PROCESO, 'En Proceso'),
        (APROBADO, 'Aprobado'),
        (RECHAZADO, 'Rechazado'),
        (COMPLETADO, 'Completado'),
    ]


class TipoSolicitud:
    """Tipos de solicitudes"""
    CREACION = 'CREACION'
    MODIFICACION = 'MODIFICACION'
    REVISION = 'REVISION'
    ELIMINACION = 'ELIMINACION'
    
    CHOICES = [
        (CREACION, 'Creación'),
        (MODIFICACION, 'Modificación'),
        (REVISION, 'Revisión'),
        (ELIMINACION, 'Eliminación'),
    ]


class TipoPaso:
    """Tipos de pasos en el flujo"""
    CREADO = 'CREADO'
    ENVIADO_REVISION = 'ENVIADO_REVISION'
    REVISADO = 'REVISADO'
    APROBADO = 'APROBADO'
    FIRMADO = 'FIRMADO'
    RECHAZADO = 'RECHAZADO'
    MODIFICADO = 'MODIFICADO'
    
    CHOICES = [
        (CREADO, 'Documento Creado'),
        (ENVIADO_REVISION, 'Enviado a Revisión'),
        (REVISADO, 'Revisado'),
        (APROBADO, 'Aprobado'),
        (FIRMADO, 'Firmado'),
        (RECHAZADO, 'Rechazado'),
        (MODIFICADO, 'Modificado'),
    ]

class Documento(models.Model):
    """Modelo principal para documentos"""
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, choices=TipoDocumento.CHOICES)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')
    estado = models.CharField(max_length=20, choices=EstadoDocumento.CHOICES, default=EstadoDocumento.BORRADOR)
    archivo = models.FileField(upload_to='documentos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documentos_documento'

    def __str__(self):
        return f"{self.titulo} - {self.tipo}"


class VersionDocumento(models.Model):
    """Modelo para versiones de documentos"""
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='versiones')
    numero_version = models.PositiveIntegerField(default=1)
    archivo = models.FileField(upload_to='versiones/')
    vigente = models.BooleanField(default=True)
    comentarios = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'documentos_version'
        unique_together = ['documento', 'numero_version']
        ordering = ['-numero_version']

    def __str__(self):
        return f"{self.documento.titulo} v{self.numero_version}"


class SolicitudDocumento(models.Model):
    """Modelo para solicitudes de documentos"""
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes')
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TipoSolicitud.CHOICES)
    estado = models.CharField(max_length=20, choices=EstadoSolicitud.CHOICES, default=EstadoSolicitud.PENDIENTE)
    numero_seguimiento = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    respondido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_respondidas')

    class Meta:
        db_table = 'documentos_solicitud'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Solicitud {self.numero_seguimiento} - {self.tipo}"


class FlujoDocumento(models.Model):
    """Modelo para el flujo de aprobación de documentos"""
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='flujo')
    paso = models.CharField(max_length=20, choices=TipoPaso.CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    detalle = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    datos_adicionales = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'documentos_flujo'
        ordering = ['fecha']

    def __str__(self):
        return f"{self.documento.titulo} - {self.paso} por {self.usuario.username}"
