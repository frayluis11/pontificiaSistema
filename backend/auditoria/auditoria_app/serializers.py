"""
Serializers para el microservicio de auditoría
"""

from rest_framework import serializers
from .models import ActividadSistema


class ActividadSistemaSerializer(serializers.ModelSerializer):
    """
    Serializer para lectura de actividades del sistema
    """
    
    class Meta:
        model = ActividadSistema
        fields = [
            'id',
            'usuario_id',
            'usuario_email', 
            'accion',
            'recurso',
            'recurso_id',
            'detalle',
            'fecha_hora',
            'ip_address',
            'user_agent',
            'session_id',
            'exito',
            'codigo_estado',
            'mensaje_error',
            'duracion_ms',
            'microservicio',
            'criticidad',
            'context',
            'tags'
        ]
        read_only_fields = ['id', 'fecha_hora']
    
    def to_representation(self, instance):
        """
        Personalizar representación del objeto
        """
        data = super().to_representation(instance)
        
        # Formatear duración para legibilidad
        if data.get('duracion_ms'):
            if data['duracion_ms'] > 1000:
                data['duracion_formatted'] = f"{data['duracion_ms'] / 1000:.2f}s"
            else:
                data['duracion_formatted'] = f"{data['duracion_ms']}ms"
        
        # Agregar etiqueta de criticidad legible
        criticidad_labels = {
            'LOW': 'Baja',
            'MEDIUM': 'Media',
            'HIGH': 'Alta',
            'CRITICAL': 'Crítica'
        }
        data['criticidad_label'] = criticidad_labels.get(data.get('criticidad'), 'Desconocida')
        
        # Agregar etiqueta de acción legible
        accion_labels = {
            'CREATE': 'Crear',
            'READ': 'Leer',
            'UPDATE': 'Actualizar', 
            'DELETE': 'Eliminar',
            'LOGIN': 'Iniciar Sesión',
            'LOGOUT': 'Cerrar Sesión',
            'UPLOAD': 'Subir Archivo',
            'DOWNLOAD': 'Descargar',
            'EXPORT': 'Exportar',
            'IMPORT': 'Importar',
            'ACCESS_DENIED': 'Acceso Denegado',
            'ERROR': 'Error',
            'OTHER': 'Otro'
        }
        data['accion_label'] = accion_labels.get(data.get('accion'), 'Desconocida')
        
        # Agregar etiqueta de recurso legible
        recurso_labels = {
            'USERS': 'Usuarios',
            'USER_PROFILE': 'Perfil de Usuario',
            'DOCUMENTS': 'Documentos',
            'PAYMENTS': 'Pagos',
            'ATTENDANCE': 'Asistencias',
            'REPORTS': 'Reportes',
            'AUDIT': 'Auditoría',
            'AUTH': 'Autenticación',
            'SYSTEM': 'Sistema',
            'API': 'API',
            'OTHER': 'Otro'
        }
        data['recurso_label'] = recurso_labels.get(data.get('recurso'), 'Desconocido')
        
        return data


class ActividadSistemaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de actividades del sistema
    Solo usado internamente por el sistema de auditoría
    """
    
    class Meta:
        model = ActividadSistema
        fields = [
            'usuario_id',
            'usuario_email',
            'accion',
            'recurso', 
            'recurso_id',
            'detalle',
            'ip_address',
            'user_agent',
            'session_id',
            'exito',
            'codigo_estado',
            'mensaje_error',
            'duracion_ms',
            'microservicio',
            'criticidad',
            'context',
            'tags'
        ]
    
    def validate_accion(self, value):
        """
        Validar acción
        """
        acciones_validas = [choice[0] for choice in ActividadSistema.ACCION_CHOICES]
        if value not in acciones_validas:
            raise serializers.ValidationError(f"Acción '{value}' no es válida. Opciones: {acciones_validas}")
        return value
    
    def validate_recurso(self, value):
        """
        Validar recurso
        """
        recursos_validos = [choice[0] for choice in ActividadSistema.RECURSO_CHOICES]
        if value not in recursos_validos:
            raise serializers.ValidationError(f"Recurso '{value}' no es válido. Opciones: {recursos_validos}")
        return value
    
    def validate_criticidad(self, value):
        """
        Validar criticidad
        """
        if value:
            criticidades_validas = [choice[0] for choice in ActividadSistema.CRITICIDAD_CHOICES]
            if value not in criticidades_validas:
                raise serializers.ValidationError(f"Criticidad '{value}' no es válida. Opciones: {criticidades_validas}")
        return value
    
    def validate_microservicio(self, value):
        """
        Validar microservicio
        """
        if value:
            microservicios_validos = [choice[0] for choice in ActividadSistema.MICROSERVICIO_CHOICES]
            if value not in microservicios_validos:
                raise serializers.ValidationError(f"Microservicio '{value}' no es válido. Opciones: {microservicios_validos}")
        return value


class ActividadSistemaListSerializer(ActividadSistemaSerializer):
    """
    Serializer optimizado para listados de actividades
    Incluye menos campos para mejorar performance
    """
    
    class Meta(ActividadSistemaSerializer.Meta):
        fields = [
            'id',
            'usuario_id',
            'usuario_email',
            'accion',
            'recurso',
            'fecha_hora',
            'exito',
            'microservicio',
            'criticidad'
        ]


class EstadisticasSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de auditoría
    """
    total_actividades = serializers.IntegerField()
    actividades_exitosas = serializers.IntegerField()
    actividades_fallidas = serializers.IntegerField()
    tasa_exito = serializers.FloatField()
    usuarios_unicos = serializers.IntegerField()
    duracion_promedio = serializers.FloatField()
    
    # Estadísticas por acción
    por_accion = serializers.DictField()
    
    # Estadísticas por recurso
    por_recurso = serializers.DictField()
    
    # Estadísticas por microservicio
    por_microservicio = serializers.DictField()
    
    # Estadísticas por criticidad
    por_criticidad = serializers.DictField()
    
    # Actividades recientes
    actividades_recientes = ActividadSistemaListSerializer(many=True)


class MetricasRendimientoSerializer(serializers.Serializer):
    """
    Serializer para métricas de rendimiento
    """
    requests_por_segundo = serializers.FloatField()
    tiempo_respuesta_promedio = serializers.FloatField()
    tiempo_respuesta_p95 = serializers.FloatField()
    tiempo_respuesta_p99 = serializers.FloatField()
    
    # Por endpoint
    endpoints_mas_lentos = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Por usuario
    usuarios_mas_activos = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Errores
    tasa_error = serializers.FloatField()
    errores_comunes = serializers.ListField(
        child=serializers.DictField()
    )


class WebhookPayloadSerializer(serializers.Serializer):
    """
    Serializer base para payloads de webhooks
    """
    action = serializers.CharField(max_length=50)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    details = serializers.DictField(required=False, default=dict)
    timestamp = serializers.DateTimeField(required=False)


class DocumentWebhookSerializer(WebhookPayloadSerializer):
    """
    Serializer para webhooks de documentos
    """
    document_id = serializers.CharField(max_length=255)


class PaymentWebhookSerializer(WebhookPayloadSerializer):
    """
    Serializer para webhooks de pagos
    """
    payment_id = serializers.CharField(max_length=255)


class UserWebhookSerializer(WebhookPayloadSerializer):
    """
    Serializer para webhooks de usuarios
    """
    user_id = serializers.IntegerField()


class AttendanceWebhookSerializer(WebhookPayloadSerializer):
    """
    Serializer para webhooks de asistencias
    """
    attendance_id = serializers.CharField(max_length=255)


class GenericWebhookSerializer(serializers.Serializer):
    """
    Serializer para webhooks genéricos
    """
    event_type = serializers.CharField(max_length=100)
    resource = serializers.CharField(max_length=50)
    resource_id = serializers.CharField(max_length=255)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    details = serializers.DictField(required=False, default=dict)
    microservice = serializers.CharField(max_length=50, default='UNKNOWN')
    timestamp = serializers.DateTimeField(required=False)