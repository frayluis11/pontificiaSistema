from rest_framework import serializers
from .models import RegistroHora, JustificacionAusencia
from datetime import time

class RegistroHoraSerializer(serializers.ModelSerializer):
    """Serializer para RegistroHora"""
    
    class Meta:
        model = RegistroHora
        fields = [
            'id', 'docente_id', 'aula', 'seccion', 'fecha', 
            'hora_entrada', 'hora_salida', 'estado', 'minutos_tardanza',
            'descuento_aplicado', 'observacion', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'minutos_tardanza', 'descuento_aplicado', 'fecha_creacion', 'fecha_actualizacion']

class RegistrarAsistenciaSerializer(serializers.Serializer):
    """Serializer para registrar asistencia"""
    docente_id = serializers.IntegerField(min_value=1)
    aula = serializers.CharField(max_length=10)
    seccion = serializers.CharField(max_length=10)
    hora_entrada = serializers.TimeField(required=False)
    
    def validate_aula(self, value):
        """Validar formato de aula"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El aula no puede estar vacía")
        return value.strip().upper()
    
    def validate_seccion(self, value):
        """Validar formato de sección"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("La sección no puede estar vacía")
        return value.strip().upper()
    
    def validate_hora_entrada(self, value):
        """Validar hora de entrada"""
        if value and (value < time(6, 0) or value > time(12, 0)):
            raise serializers.ValidationError("La hora de entrada debe estar entre 6:00 AM y 12:00 PM")
        return value

class ActualizarSalidaSerializer(serializers.Serializer):
    """Serializer para actualizar hora de salida"""
    registro_id = serializers.IntegerField(min_value=1)
    hora_salida = serializers.TimeField(required=False)
    
    def validate_hora_salida(self, value):
        """Validar hora de salida"""
        if value and (value < time(8, 0) or value > time(18, 0)):
            raise serializers.ValidationError("La hora de salida debe estar entre 8:00 AM y 6:00 PM")
        return value

class HistorialAsistenciaSerializer(serializers.Serializer):
    """Serializer para consultar historial"""
    docente_id = serializers.IntegerField(min_value=1)
    fecha_inicio = serializers.DateField(required=False)
    fecha_fin = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validar rango de fechas"""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise serializers.ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin")
        
        return data

class MarcarAusenciaSerializer(serializers.Serializer):
    """Serializer para marcar ausencia"""
    docente_id = serializers.IntegerField(min_value=1)
    fecha = serializers.DateField()
    observacion = serializers.CharField(max_length=255, required=False, allow_blank=True)

class JustificacionAusenciaSerializer(serializers.ModelSerializer):
    """Serializer completo para JustificacionAusencia"""
    
    class Meta:
        model = JustificacionAusencia
        fields = [
            'id', 'docente_id', 'fecha', 'motivo', 'tipo_motivo',
            'documentos_adjuntos', 'estado', 'fecha_revision', 'revisor_id',
            'comentario_revisor', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'estado', 'fecha_revision', 'revisor_id', 
            'comentario_revisor', 'fecha_creacion', 'fecha_actualizacion'
        ]

class CrearJustificacionSerializer(serializers.Serializer):
    """Serializer para crear justificación"""
    docente_id = serializers.IntegerField(min_value=1)
    fecha = serializers.DateField()
    motivo = serializers.CharField(max_length=500)
    tipo_motivo = serializers.ChoiceField(
        choices=JustificacionAusencia.TIPO_MOTIVO_CHOICES,
        default='OTROS'
    )
    documentos_adjuntos = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_motivo(self, value):
        """Validar motivo"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("El motivo debe tener al menos 10 caracteres")
        return value.strip()

class ProcesarJustificacionSerializer(serializers.Serializer):
    """Serializer para procesar (aprobar/rechazar) justificación"""
    accion = serializers.ChoiceField(choices=['APROBAR', 'RECHAZAR'])
    revisor_id = serializers.IntegerField(min_value=1)
    comentario_revisor = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_comentario_revisor(self, value):
        """Validar comentario del revisor"""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("El comentario debe tener al menos 5 caracteres")
        return value.strip() if value else None

class EstadisticasAsistenciaSerializer(serializers.Serializer):
    """Serializer para estadísticas de asistencia"""
    docente_id = serializers.IntegerField(min_value=1)
    fecha_inicio = serializers.DateField(required=False)
    fecha_fin = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validar rango de fechas"""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise serializers.ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin")
        
        return data

class CambiarEstrategiaSerializer(serializers.Serializer):
    """Serializer para cambiar estrategia de descuento"""
    tipo_estrategia = serializers.ChoiceField(
        choices=['lineal', 'escalonado', 'progresivo', 'semanal']
    )

# Serializers de respuesta para APIs
class RespuestaRegistroSerializer(serializers.Serializer):
    """Serializer para respuesta de registro de asistencia"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = RegistroHoraSerializer(required=False)
    descuento_aplicado = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    minutos_tardanza = serializers.IntegerField(required=False)

class RespuestaHistorialSerializer(serializers.Serializer):
    """Serializer para respuesta de historial"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = RegistroHoraSerializer(many=True, required=False)
    total_registros = serializers.IntegerField(required=False)

class RespuestaJustificacionSerializer(serializers.Serializer):
    """Serializer para respuesta de justificación"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = JustificacionAusenciaSerializer(required=False)

class RespuestaEstadisticasSerializer(serializers.Serializer):
    """Serializer para respuesta de estadísticas"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False)
