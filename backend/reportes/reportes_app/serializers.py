"""
DTOs y Serializers para el microservicio de reportes
"""

from rest_framework import serializers
from django.utils import timezone
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import json

from .models import Reporte, Metrica, ReporteMetrica
from .exceptions import ParametrosInvalidosException


# ========== DTOs (Data Transfer Objects) ==========

class ReporteDTO:
    """DTO para transferencia de datos de reportes"""
    
    def __init__(
        self,
        id: str = None,
        tipo: str = None,
        parametros: Dict[str, Any] = None,
        formato: str = None,
        autor_id: int = None,
        estado: str = None,
        archivo: str = None,
        fecha_creacion: datetime = None,
        fecha_actualizacion: datetime = None,
        expires_at: datetime = None,
        titulo: str = None
    ):
        self.id = id
        self.tipo = tipo
        self.parametros = parametros or {}
        self.formato = formato
        self.autor_id = autor_id
        self.estado = estado
        self.archivo = archivo
        self.fecha_creacion = fecha_creacion
        self.fecha_actualizacion = fecha_actualizacion
        self.expires_at = expires_at
        self.titulo = titulo
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el DTO a diccionario"""
        return {
            'id': self.id,
            'tipo': self.tipo,
            'parametros': self.parametros,
            'formato': self.formato,
            'autor_id': self.autor_id,
            'estado': self.estado,
            'archivo': self.archivo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'titulo': self.titulo
        }
    
    @classmethod
    def from_model(cls, reporte: Reporte) -> 'ReporteDTO':
        """Crea un DTO desde un modelo de Reporte"""
        return cls(
            id=reporte.id,
            tipo=reporte.tipo,
            parametros=reporte.parametros,
            formato=reporte.formato,
            autor_id=reporte.autor_id,
            estado=reporte.estado,
            archivo=reporte.archivo.name if reporte.archivo else None,
            fecha_creacion=reporte.fecha_creacion,
            fecha_actualizacion=reporte.fecha_actualizacion,
            expires_at=reporte.expires_at,
            titulo=reporte.titulo
        )


class MetricaDTO:
    """DTO para transferencia de datos de métricas"""
    
    def __init__(
        self,
        id: int = None,
        nombre: str = None,
        valor: float = None,
        periodo: str = None,
        fecha_calculo: datetime = None,
        metadatos: Dict[str, Any] = None,
        activa: bool = True
    ):
        self.id = id
        self.nombre = nombre
        self.valor = valor
        self.periodo = periodo
        self.fecha_calculo = fecha_calculo
        self.metadatos = metadatos or {}
        self.activa = activa
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el DTO a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'valor': self.valor,
            'periodo': self.periodo,
            'fecha_calculo': self.fecha_calculo.isoformat() if self.fecha_calculo else None,
            'metadatos': self.metadatos,
            'activa': self.activa
        }
    
    @classmethod
    def from_model(cls, metrica: Metrica) -> 'MetricaDTO':
        """Crea un DTO desde un modelo de Métrica"""
        return cls(
            id=metrica.id,
            nombre=metrica.nombre,
            valor=metrica.valor,
            periodo=metrica.periodo,
            fecha_calculo=metrica.fecha_calculo,
            metadatos=metrica.metadatos,
            activa=metrica.activa
        )


class ReporteResumenDTO:
    """DTO para resumen de reporte (listados)"""
    
    def __init__(
        self,
        id: str,
        tipo: str,
        formato: str,
        estado: str,
        titulo: str,
        fecha_creacion: datetime,
        expires_at: datetime = None,
        tamaño_archivo: int = None
    ):
        self.id = id
        self.tipo = tipo
        self.formato = formato
        self.estado = estado
        self.titulo = titulo
        self.fecha_creacion = fecha_creacion
        self.expires_at = expires_at
        self.tamaño_archivo = tamaño_archivo
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tipo': self.tipo,
            'formato': self.formato,
            'estado': self.estado,
            'titulo': self.titulo,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'tamaño_archivo': self.tamaño_archivo
        }


# ========== Serializers ==========

class ParametrosReporteSerializer(serializers.Serializer):
    """Serializer para validar parámetros de reportes"""
    
    fecha_inicio = serializers.DateField(required=False, help_text="Fecha de inicio del período")
    fecha_fin = serializers.DateField(required=False, help_text="Fecha de fin del período")
    usuario_id = serializers.IntegerField(required=False, help_text="ID del usuario específico")
    departamento = serializers.CharField(max_length=100, required=False, help_text="Departamento a filtrar")
    incluir_graficos = serializers.BooleanField(default=True, help_text="Incluir gráficos en el reporte")
    nivel_detalle = serializers.ChoiceField(
        choices=['basico', 'intermedio', 'detallado'],
        default='intermedio',
        help_text="Nivel de detalle del reporte"
    )
    metricas = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="Lista de métricas específicas a incluir"
    )
    filtros_adicionales = serializers.JSONField(
        required=False,
        help_text="Filtros adicionales en formato JSON"
    )
    
    def validate(self, data):
        """Validaciones generales de parámetros"""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise serializers.ValidationError(
                    "La fecha de inicio no puede ser posterior a la fecha de fin"
                )
            
            # Validar que no sea un rango muy amplio (más de 2 años)
            diff = fecha_fin - fecha_inicio
            if diff.days > 730:
                raise serializers.ValidationError(
                    "El rango de fechas no puede ser mayor a 2 años"
                )
        
        return data


class CrearReporteSerializer(serializers.Serializer):
    """Serializer para crear un nuevo reporte"""
    
    tipo = serializers.ChoiceField(
        choices=[
            ('ventas', 'Reporte de Ventas'),
            ('usuarios', 'Reporte de Usuarios'),
            ('metricas', 'Reporte de Métricas'),
            ('financiero', 'Reporte Financiero'),
            ('academico', 'Reporte Académico'),
            ('asistencia', 'Reporte de Asistencia'),
            ('calificaciones', 'Reporte de Calificaciones'),
            ('personalizado', 'Reporte Personalizado')
        ],
        help_text="Tipo de reporte a generar"
    )
    
    formato = serializers.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV')],
        default='pdf',
        help_text="Formato de salida del reporte"
    )
    
    titulo = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Título personalizado para el reporte"
    )
    
    parametros = ParametrosReporteSerializer(required=False)
    
    asincrono = serializers.BooleanField(
        default=True,
        help_text="Si el reporte debe procesarse de forma asíncrona"
    )
    
    notificar_completado = serializers.BooleanField(
        default=False,
        help_text="Enviar notificación cuando el reporte esté listo"
    )
    
    def validate_parametros(self, value):
        """Validar parámetros específicos según el tipo de reporte"""
        if not value:
            return {}
        
        # Serializar los parámetros para validación
        serializer = ParametrosReporteSerializer(data=value)
        if serializer.is_valid():
            return serializer.validated_data
        else:
            raise serializers.ValidationError(serializer.errors)


class ReporteSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Reporte"""
    
    parametros = serializers.JSONField(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiempo_procesamiento = serializers.SerializerMethodField()
    tamaño_archivo = serializers.SerializerMethodField()
    url_descarga = serializers.SerializerMethodField()
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'tipo', 'parametros', 'formato', 'autor_id',
            'estado', 'estado_display', 'archivo', 'fecha_creacion',
            'fecha_actualizacion', 'expires_at', 'titulo',
            'tiempo_procesamiento', 'tamaño_archivo', 'url_descarga'
        ]
        read_only_fields = [
            'id', 'fecha_creacion', 'fecha_actualizacion',
            'estado', 'archivo'
        ]
    
    def get_tiempo_procesamiento(self, obj) -> Optional[float]:
        """Calcula el tiempo de procesamiento en segundos"""
        if obj.estado == 'completado' and obj.fecha_actualizacion:
            delta = obj.fecha_actualizacion - obj.fecha_creacion
            return delta.total_seconds()
        return None
    
    def get_tamaño_archivo(self, obj) -> Optional[int]:
        """Obtiene el tamaño del archivo en bytes"""
        if obj.archivo:
            try:
                return obj.archivo.size
            except:
                return None
        return None
    
    def get_url_descarga(self, obj) -> Optional[str]:
        """Genera URL de descarga si el archivo existe"""
        if obj.archivo and obj.estado == 'completado':
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo.url)
        return None


class ReporteResumenSerializer(serializers.ModelSerializer):
    """Serializer resumido para listados de reportes"""
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tamaño_archivo = serializers.SerializerMethodField()
    expirado = serializers.SerializerMethodField()
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'tipo', 'formato', 'estado', 'estado_display',
            'titulo', 'fecha_creacion', 'expires_at',
            'tamaño_archivo', 'expirado'
        ]
    
    def get_tamaño_archivo(self, obj) -> Optional[int]:
        """Obtiene el tamaño del archivo en bytes"""
        if obj.archivo:
            try:
                return obj.archivo.size
            except:
                return None
        return None
    
    def get_expirado(self, obj) -> bool:
        """Indica si el reporte está expirado"""
        return obj.esta_expirado()


class MetricaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Métrica"""
    
    tendencia = serializers.SerializerMethodField()
    formato_valor = serializers.SerializerMethodField()
    
    class Meta:
        model = Metrica
        fields = [
            'id', 'nombre', 'valor', 'periodo', 'fecha_calculo',
            'metadatos', 'activa', 'tendencia', 'formato_valor'
        ]
        read_only_fields = ['id', 'fecha_calculo']
    
    def get_tendencia(self, obj) -> Optional[str]:
        """Calcula la tendencia de la métrica"""
        try:
            # Buscar métrica anterior del mismo tipo
            metrica_anterior = Metrica.objects.filter(
                nombre=obj.nombre,
                periodo=obj.periodo,
                fecha_calculo__lt=obj.fecha_calculo,
                activa=True
            ).order_by('-fecha_calculo').first()
            
            if metrica_anterior:
                if obj.valor > metrica_anterior.valor:
                    return 'ascendente'
                elif obj.valor < metrica_anterior.valor:
                    return 'descendente'
                else:
                    return 'estable'
            return 'sin_datos'
        except:
            return 'sin_datos'
    
    def get_formato_valor(self, obj) -> str:
        """Formatea el valor según el tipo de métrica"""
        metadatos = obj.metadatos or {}
        formato = metadatos.get('formato', 'decimal')
        
        if formato == 'porcentaje':
            return f"{obj.valor:.2f}%"
        elif formato == 'moneda':
            return f"${obj.valor:,.2f}"
        elif formato == 'entero':
            return f"{int(obj.valor):,}"
        else:
            return f"{obj.valor:.2f}"


class ExportarMetricasSerializer(serializers.Serializer):
    """Serializer para exportar métricas"""
    
    nombres = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="Lista de nombres de métricas a exportar"
    )
    
    periodo = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Período específico a exportar"
    )
    
    fecha_desde = serializers.DateField(
        required=False,
        help_text="Fecha desde para filtrar métricas"
    )
    
    fecha_hasta = serializers.DateField(
        required=False,
        help_text="Fecha hasta para filtrar métricas"
    )
    
    formato = serializers.ChoiceField(
        choices=[('excel', 'Excel'), ('csv', 'CSV'), ('json', 'JSON')],
        default='excel',
        help_text="Formato de exportación"
    )
    
    incluir_graficos = serializers.BooleanField(
        default=True,
        help_text="Incluir gráficos en la exportación"
    )
    
    solo_activas = serializers.BooleanField(
        default=True,
        help_text="Solo exportar métricas activas"
    )
    
    def validate(self, data):
        """Validaciones para exportación de métricas"""
        fecha_desde = data.get('fecha_desde')
        fecha_hasta = data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise serializers.ValidationError(
                    "La fecha desde no puede ser posterior a la fecha hasta"
                )
        
        return data


class EstadisticasReporteSerializer(serializers.Serializer):
    """Serializer para estadísticas de reportes"""
    
    total_reportes = serializers.IntegerField(read_only=True)
    reportes_completados = serializers.IntegerField(read_only=True)
    reportes_pendientes = serializers.IntegerField(read_only=True)
    reportes_error = serializers.IntegerField(read_only=True)
    tiempo_promedio_procesamiento = serializers.FloatField(read_only=True)
    tipos_mas_solicitados = serializers.ListField(read_only=True)
    formatos_preferidos = serializers.DictField(read_only=True)
    
    def to_representation(self, instance):
        """Personaliza la representación de las estadísticas"""
        data = super().to_representation(instance)
        
        # Agregar porcentajes
        total = data.get('total_reportes', 0)
        if total > 0:
            data['porcentaje_completados'] = (data.get('reportes_completados', 0) / total) * 100
            data['porcentaje_pendientes'] = (data.get('reportes_pendientes', 0) / total) * 100
            data['porcentaje_error'] = (data.get('reportes_error', 0) / total) * 100
        
        return data


# ========== Serializers de Respuesta ==========

class RespuestaReporteSerializer(serializers.Serializer):
    """Serializer para respuestas de creación de reportes"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    reporte_id = serializers.CharField(required=False)
    estado = serializers.CharField(required=False)
    url_seguimiento = serializers.CharField(required=False)
    tiempo_estimado = serializers.IntegerField(required=False, help_text="Tiempo estimado en segundos")


class ErrorReporteSerializer(serializers.Serializer):
    """Serializer para errores de reportes"""
    
    error = serializers.CharField()
    codigo = serializers.CharField(required=False)
    detalles = serializers.DictField(required=False)
    sugerencias = serializers.ListField(child=serializers.CharField(), required=False)