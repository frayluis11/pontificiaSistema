"""
Modelos para el microservicio de auditoría
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator
import json
import uuid


class ActividadSistema(models.Model):
    """
    Modelo para registrar todas las actividades del sistema
    
    Registra automáticamente:
    - Acciones de usuarios (login, logout, CRUD operations)
    - Cambios en documentos y pagos
    - Accesos a endpoints
    - Errores y excepciones
    """
    
    # Tipos de acciones
    TIPO_ACCION_CHOICES = [
        # Autenticación
        ('LOGIN', 'Inicio de Sesión'),
        ('LOGOUT', 'Cierre de Sesión'),
        ('LOGIN_FAILED', 'Intento de Login Fallido'),
        
        # CRUD Operations
        ('CREATE', 'Crear'),
        ('READ', 'Leer/Consultar'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        
        # Operaciones específicas
        ('UPLOAD', 'Cargar Archivo'),
        ('DOWNLOAD', 'Descargar Archivo'),
        ('EXPORT', 'Exportar Datos'),
        ('IMPORT', 'Importar Datos'),
        
        # Cambios de estado
        ('STATUS_CHANGE', 'Cambio de Estado'),
        ('APPROVE', 'Aprobar'),
        ('REJECT', 'Rechazar'),
        
        # Errores y excepciones
        ('ERROR', 'Error del Sistema'),
        ('WARNING', 'Advertencia'),
        ('EXCEPTION', 'Excepción'),
        
        # Accesos
        ('ACCESS_GRANTED', 'Acceso Concedido'),
        ('ACCESS_DENIED', 'Acceso Denegado'),
        
        # Otros
        ('OTHER', 'Otra Acción'),
    ]
    
    # Niveles de criticidad
    NIVEL_CRITICIDAD_CHOICES = [
        ('LOW', 'Bajo'),
        ('MEDIUM', 'Medio'),
        ('HIGH', 'Alto'),
        ('CRITICAL', 'Crítico'),
    ]
    
    # Recursos del sistema
    RECURSO_CHOICES = [
        # Microservicios
        ('AUTH', 'Autenticación'),
        ('USERS', 'Usuarios'),
        ('DOCUMENTS', 'Documentos'),
        ('PAYMENTS', 'Pagos'),
        ('ATTENDANCE', 'Asistencia'),
        ('REPORTS', 'Reportes'),
        ('AUDIT', 'Auditoría'),
        
        # Entidades específicas
        ('USER_PROFILE', 'Perfil de Usuario'),
        ('DOCUMENT_FILE', 'Archivo de Documento'),
        ('PAYMENT_TRANSACTION', 'Transacción de Pago'),
        ('ATTENDANCE_RECORD', 'Registro de Asistencia'),
        ('REPORT_GENERATION', 'Generación de Reporte'),
        
        # Sistema
        ('SYSTEM', 'Sistema'),
        ('DATABASE', 'Base de Datos'),
        ('API', 'API'),
        ('MIDDLEWARE', 'Middleware'),
        
        # Otros
        ('OTHER', 'Otro Recurso'),
    ]
    
    # Campos principales
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único de la actividad"
    )
    
    usuario_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID del usuario que realizó la acción (null para usuarios anónimos)"
    )
    
    usuario_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Email del usuario para facilitar búsquedas"
    )
    
    accion = models.CharField(
        max_length=50,
        choices=TIPO_ACCION_CHOICES,
        help_text="Tipo de acción realizada"
    )
    
    recurso = models.CharField(
        max_length=100,
        choices=RECURSO_CHOICES,
        help_text="Recurso afectado por la acción"
    )
    
    recurso_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID específico del recurso afectado"
    )
    
    fecha = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Fecha y hora de la actividad"
    )
    
    detalle = models.JSONField(
        default=dict,
        help_text="Detalles adicionales de la actividad en formato JSON"
    )
    
    # Información de contexto
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Dirección IP desde donde se realizó la acción"
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent del navegador o cliente"
    )
    
    session_key = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Clave de sesión para agrupar actividades"
    )
    
    # Información HTTP
    metodo_http = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Método HTTP utilizado (GET, POST, etc.)"
    )
    
    url_solicitada = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL que fue solicitada"
    )
    
    codigo_estado = models.IntegerField(
        null=True,
        blank=True,
        help_text="Código de estado HTTP de la respuesta"
    )
    
    # Información adicional
    nivel_criticidad = models.CharField(
        max_length=20,
        choices=NIVEL_CRITICIDAD_CHOICES,
        default='LOW',
        help_text="Nivel de criticidad de la actividad"
    )
    
    duracion_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duración de la operación en milisegundos"
    )
    
    exito = models.BooleanField(
        default=True,
        help_text="Indica si la operación fue exitosa"
    )
    
    mensaje_error = models.TextField(
        null=True,
        blank=True,
        help_text="Mensaje de error si la operación falló"
    )
    
    # Metadatos
    microservicio = models.CharField(
        max_length=50,
        default='AUDIT',
        help_text="Microservicio que generó el log"
    )
    
    version_api = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Versión de la API utilizada"
    )
    
    tags = models.JSONField(
        default=list,
        help_text="Tags para categorizar y filtrar actividades"
    )
    
    class Meta:
        db_table = 'auditoria_actividad_sistema'
        verbose_name = 'Actividad del Sistema'
        verbose_name_plural = 'Actividades del Sistema'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['usuario_id']),
            models.Index(fields=['accion']),
            models.Index(fields=['recurso']),
            models.Index(fields=['nivel_criticidad']),
            models.Index(fields=['exito']),
            models.Index(fields=['microservicio']),
            models.Index(fields=['fecha', 'usuario_id']),
            models.Index(fields=['accion', 'recurso']),
        ]
    
    def __str__(self):
        """Representación string de la actividad"""
        usuario_info = f"Usuario {self.usuario_id}" if self.usuario_id else "Usuario anónimo"
        return f"{self.get_accion_display()} en {self.get_recurso_display()} - {usuario_info} ({self.fecha.strftime('%Y-%m-%d %H:%M:%S')})"
    
    def save(self, *args, **kwargs):
        """Override save para validaciones adicionales"""
        # Validar que el detalle sea un diccionario válido
        if self.detalle and not isinstance(self.detalle, dict):
            try:
                self.detalle = json.loads(self.detalle)
            except (json.JSONDecodeError, TypeError):
                self.detalle = {'raw_data': str(self.detalle)}
        
        # Validar que tags sea una lista
        if self.tags and not isinstance(self.tags, list):
            try:
                self.tags = json.loads(self.tags) if isinstance(self.tags, str) else []
            except (json.JSONDecodeError, TypeError):
                self.tags = []
        
        # Truncar campos largos
        if self.user_agent and len(self.user_agent) > 1000:
            self.user_agent = self.user_agent[:1000]
        
        if self.mensaje_error and len(self.mensaje_error) > 5000:
            self.mensaje_error = self.mensaje_error[:5000]
        
        super().save(*args, **kwargs)
    
    def get_detalle_formatted(self):
        """Obtiene el detalle formateado para mostrar"""
        if not self.detalle:
            return "No hay detalles"
        
        try:
            if isinstance(self.detalle, dict):
                formatted = []
                for key, value in self.detalle.items():
                    formatted.append(f"{key}: {value}")
                return "; ".join(formatted)
            else:
                return str(self.detalle)
        except:
            return "Error al formatear detalles"
    
    def is_critical_activity(self):
        """Determina si la actividad es crítica"""
        critical_actions = ['DELETE', 'LOGIN_FAILED', 'ERROR', 'EXCEPTION', 'ACCESS_DENIED']
        return self.accion in critical_actions or self.nivel_criticidad in ['HIGH', 'CRITICAL']
    
    def get_duration_display(self):
        """Obtiene la duración formateada"""
        if not self.duracion_ms:
            return "N/A"
        
        if self.duracion_ms < 1000:
            return f"{self.duracion_ms}ms"
        elif self.duracion_ms < 60000:
            return f"{self.duracion_ms/1000:.2f}s"
        else:
            return f"{self.duracion_ms/60000:.2f}min"
    
    def add_tag(self, tag):
        """Agregar un tag a la actividad"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag):
        """Remover un tag de la actividad"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    @classmethod
    def crear_actividad(cls, usuario_id=None, accion='OTHER', recurso='OTHER', 
                       detalle=None, **kwargs):
        """
        Método de conveniencia para crear actividades
        
        Args:
            usuario_id: ID del usuario
            accion: Tipo de acción
            recurso: Recurso afectado
            detalle: Detalles adicionales
            **kwargs: Otros parámetros
        """
        return cls.objects.create(
            usuario_id=usuario_id,
            accion=accion,
            recurso=recurso,
            detalle=detalle or {},
            **kwargs
        )
    
    @classmethod
    def log_login(cls, usuario_id, ip_address=None, user_agent=None, exito=True):
        """Registrar login de usuario"""
        accion = 'LOGIN' if exito else 'LOGIN_FAILED'
        nivel = 'LOW' if exito else 'HIGH'
        
        return cls.crear_actividad(
            usuario_id=usuario_id,
            accion=accion,
            recurso='AUTH',
            ip_address=ip_address,
            user_agent=user_agent,
            nivel_criticidad=nivel,
            exito=exito,
            detalle={'login_attempt': True, 'success': exito}
        )
    
    @classmethod
    def log_crud_operation(cls, usuario_id, accion, recurso, recurso_id=None, 
                          detalle=None, exito=True):
        """Registrar operación CRUD"""
        return cls.crear_actividad(
            usuario_id=usuario_id,
            accion=accion,
            recurso=recurso,
            recurso_id=recurso_id,
            detalle=detalle or {},
            exito=exito,
            nivel_criticidad='MEDIUM' if accion == 'DELETE' else 'LOW'
        )
    
    @classmethod
    def log_error(cls, usuario_id, recurso, mensaje_error, detalle=None):
        """Registrar error del sistema"""
        return cls.crear_actividad(
            usuario_id=usuario_id,
            accion='ERROR',
            recurso=recurso,
            mensaje_error=mensaje_error,
            detalle=detalle or {},
            exito=False,
            nivel_criticidad='HIGH'
        )
