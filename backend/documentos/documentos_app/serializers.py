"""
Serializers para el servicio de documentos

Define los serializers para la API REST que convierten
entre modelos Django y representaciones JSON
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from datetime import date

from .models import (
    Documento, VersionDocumento, SolicitudDocumento, FlujoDocumento,
    EstadoDocumento, EstadoSolicitud, TipoDocumento, TipoSolicitud, TipoPaso
)


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Serializer base con campos comunes
    """
    
    id = serializers.UUIDField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_actualizacion = serializers.DateTimeField(read_only=True)
    activo = serializers.BooleanField(read_only=True)


class DocumentoListSerializer(BaseModelSerializer):
    """
    Serializer para la lista de documentos (campos básicos)
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    esta_vigente = serializers.SerializerMethodField()
    url_descarga = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id', 'titulo', 'tipo', 'tipo_display', 'estado', 'estado_display',
            'codigo_documento', 'version_actual', 'categoria', 'autor_id',
            'publico', 'confidencial', 'fecha_vigencia', 'fecha_vencimiento',
            'fecha_creacion', 'fecha_actualizacion', 'descargas', 'visualizaciones',
            'esta_vigente', 'url_descarga'
        ]
    
    def get_esta_vigente(self, obj) -> bool:
        """Indica si el documento está vigente"""
        return obj.esta_vigente()
    
    def get_url_descarga(self, obj) -> str:
        """URL para descargar el documento"""
        request = self.context.get('request')
        if request and obj.archivo:
            return request.build_absolute_uri(f'/api/documentos/{obj.id}/descargar/')
        return ''


class DocumentoDetailSerializer(BaseModelSerializer):
    """
    Serializer detallado para documentos individuales
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    esta_vigente = serializers.SerializerMethodField()
    puede_ser_editado = serializers.SerializerMethodField()
    puede_ser_aprobado = serializers.SerializerMethodField()
    puede_ser_firmado = serializers.SerializerMethodField()
    url_descarga = serializers.SerializerMethodField()
    version_vigente = serializers.SerializerMethodField()
    total_versiones = serializers.SerializerMethodField()
    tamano_archivo_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id', 'titulo', 'descripcion', 'tipo', 'tipo_display', 
            'estado', 'estado_display', 'codigo_documento', 'version_actual',
            'categoria', 'palabras_clave', 'autor_id', 'publico', 'confidencial',
            'fecha_vigencia', 'fecha_vencimiento', 'requiere_aprobacion',
            'aprobado_por', 'fecha_aprobacion', 'tamano_archivo', 'tipo_mime',
            'descargas', 'visualizaciones', 'fecha_creacion', 'fecha_actualizacion',
            'activo', 'esta_vigente', 'puede_ser_editado', 'puede_ser_aprobado',
            'puede_ser_firmado', 'url_descarga', 'version_vigente', 'total_versiones',
            'tamano_archivo_mb'
        ]
    
    def get_esta_vigente(self, obj) -> bool:
        """Indica si el documento está vigente"""
        return obj.esta_vigente()
    
    def get_puede_ser_editado(self, obj) -> bool:
        """Indica si el documento puede ser editado"""
        return obj.puede_ser_editado()
    
    def get_puede_ser_aprobado(self, obj) -> bool:
        """Indica si el documento puede ser aprobado"""
        return obj.puede_ser_aprobado()
    
    def get_puede_ser_firmado(self, obj) -> bool:
        """Indica si el documento puede ser firmado"""
        return obj.puede_ser_firmado()
    
    def get_url_descarga(self, obj) -> str:
        """URL para descargar el documento"""
        request = self.context.get('request')
        if request and obj.archivo:
            return request.build_absolute_uri(f'/api/documentos/{obj.id}/descargar/')
        return ''
    
    def get_version_vigente(self, obj):
        """Información de la versión vigente"""
        version = obj.obtener_version_vigente()
        if version:
            return {
                'id': str(version.id),
                'numero_version': str(version.numero_version),
                'fecha_creacion': version.fecha_creacion,
                'creado_por': version.creado_por,
                'comentarios': version.comentarios
            }
        return None
    
    def get_total_versiones(self, obj) -> int:
        """Total de versiones del documento"""
        return obj.versiones.filter(activo=True).count()
    
    def get_tamano_archivo_mb(self, obj) -> float:
        """Tamaño del archivo en MB"""
        if obj.tamano_archivo:
            return round(obj.tamano_archivo / (1024 * 1024), 2)
        return 0.0


class DocumentoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear documentos
    """
    
    archivo = serializers.FileField(write_only=True)
    
    class Meta:
        model = Documento
        fields = [
            'titulo', 'descripcion', 'tipo', 'categoria', 'palabras_clave',
            'publico', 'confidencial', 'fecha_vigencia', 'fecha_vencimiento',
            'requiere_aprobacion', 'archivo'
        ]
    
    def validate_archivo(self, value):
        """Valida el archivo subido"""
        from django.conf import settings
        
        # Verificar tamaño
        if value.size > settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"El archivo excede el tamaño máximo ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        # Verificar extensión
        extension = value.name.split('.')[-1].lower()
        if extension not in settings.ALLOWED_FILE_TYPES:
            raise serializers.ValidationError(
                f"Tipo de archivo no permitido: {extension}"
            )
        
        return value
    
    def validate_fecha_vencimiento(self, value):
        """Valida la fecha de vencimiento"""
        if value and value <= date.today():
            raise serializers.ValidationError(
                "La fecha de vencimiento debe ser futura"
            )
        return value
    
    def validate(self, attrs):
        """Validaciones cruzadas"""
        fecha_vigencia = attrs.get('fecha_vigencia')
        fecha_vencimiento = attrs.get('fecha_vencimiento')
        
        if fecha_vigencia and fecha_vencimiento:
            if fecha_vigencia >= fecha_vencimiento:
                raise serializers.ValidationError(
                    "La fecha de vigencia debe ser anterior a la fecha de vencimiento"
                )
        
        return attrs


class DocumentoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar documentos
    """
    
    class Meta:
        model = Documento
        fields = [
            'titulo', 'descripcion', 'categoria', 'palabras_clave',
            'publico', 'confidencial', 'fecha_vigencia', 'fecha_vencimiento'
        ]
    
    def validate_fecha_vencimiento(self, value):
        """Valida la fecha de vencimiento"""
        if value and value <= date.today():
            raise serializers.ValidationError(
                "La fecha de vencimiento debe ser futura"
            )
        return value


class VersionDocumentoSerializer(BaseModelSerializer):
    """
    Serializer para versiones de documentos
    """
    
    numero_version_str = serializers.CharField(source='numero_version', read_only=True)
    es_version_mayor = serializers.SerializerMethodField()
    tamano_archivo_mb = serializers.SerializerMethodField()
    url_descarga = serializers.SerializerMethodField()
    
    class Meta:
        model = VersionDocumento
        fields = [
            'id', 'documento', 'numero_version', 'numero_version_str',
            'vigente', 'creado_por', 'comentarios', 'tamano_archivo',
            'tipo_mime', 'hash_archivo', 'fecha_creacion', 'fecha_actualizacion',
            'es_version_mayor', 'tamano_archivo_mb', 'url_descarga'
        ]
    
    def get_es_version_mayor(self, obj) -> bool:
        """Indica si es una versión mayor"""
        return obj.es_version_mayor()
    
    def get_tamano_archivo_mb(self, obj) -> float:
        """Tamaño del archivo en MB"""
        if obj.tamano_archivo:
            return round(obj.tamano_archivo / (1024 * 1024), 2)
        return 0.0
    
    def get_url_descarga(self, obj) -> str:
        """URL para descargar la versión"""
        request = self.context.get('request')
        if request and obj.archivo:
            return request.build_absolute_uri(
                f'/api/documentos/{obj.documento.id}/versiones/{obj.id}/descargar/'
            )
        return ''


class VersionDocumentoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevas versiones
    """
    
    archivo = serializers.FileField(write_only=True)
    
    class Meta:
        model = VersionDocumento
        fields = ['archivo', 'comentarios']
    
    def validate_archivo(self, value):
        """Valida el archivo de la versión"""
        from django.conf import settings
        
        # Verificar tamaño
        if value.size > settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"El archivo excede el tamaño máximo ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        # Verificar extensión
        extension = value.name.split('.')[-1].lower()
        if extension not in settings.ALLOWED_FILE_TYPES:
            raise serializers.ValidationError(
                f"Tipo de archivo no permitido: {extension}"
            )
        
        return value


class SolicitudDocumentoListSerializer(BaseModelSerializer):
    """
    Serializer para la lista de solicitudes
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    documento_titulo = serializers.CharField(source='documento.titulo', read_only=True)
    esta_vencida = serializers.SerializerMethodField()
    tiempo_transcurrido = serializers.SerializerMethodField()
    
    class Meta:
        model = SolicitudDocumento
        fields = [
            'id', 'numero_seguimiento', 'titulo', 'tipo', 'tipo_display',
            'estado', 'estado_display', 'prioridad', 'prioridad_display',
            'solicitante_id', 'asignado_a', 'documento_titulo',
            'fecha_solicitud', 'fecha_limite', 'fecha_respuesta',
            'esta_vencida', 'tiempo_transcurrido'
        ]
    
    def get_esta_vencida(self, obj) -> bool:
        """Indica si la solicitud está vencida"""
        return obj.esta_vencida()
    
    def get_tiempo_transcurrido(self, obj) -> int:
        """Tiempo transcurrido en horas"""
        return obj.tiempo_transcurrido()


class SolicitudDocumentoDetailSerializer(BaseModelSerializer):
    """
    Serializer detallado para solicitudes individuales
    """
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    documento_info = serializers.SerializerMethodField()
    esta_vencida = serializers.SerializerMethodField()
    tiempo_transcurrido = serializers.SerializerMethodField()
    
    class Meta:
        model = SolicitudDocumento
        fields = [
            'id', 'numero_seguimiento', 'titulo', 'descripcion', 'justificacion',
            'tipo', 'tipo_display', 'estado', 'estado_display',
            'prioridad', 'prioridad_display', 'solicitante_id', 'asignado_a',
            'documento', 'documento_info', 'fecha_solicitud', 'fecha_limite',
            'fecha_respuesta', 'fecha_asignacion', 'respuesta', 'respondido_por',
            'archivo_adjunto', 'fecha_creacion', 'fecha_actualizacion',
            'esta_vencida', 'tiempo_transcurrido'
        ]
    
    def get_documento_info(self, obj):
        """Información básica del documento relacionado"""
        if obj.documento:
            return {
                'id': str(obj.documento.id),
                'titulo': obj.documento.titulo,
                'codigo': obj.documento.codigo_documento,
                'tipo': obj.documento.get_tipo_display(),
                'estado': obj.documento.get_estado_display()
            }
        return None
    
    def get_esta_vencida(self, obj) -> bool:
        """Indica si la solicitud está vencida"""
        return obj.esta_vencida()
    
    def get_tiempo_transcurrido(self, obj) -> int:
        """Tiempo transcurrido en horas"""
        return obj.tiempo_transcurrido()


class SolicitudDocumentoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear solicitudes
    """
    
    archivo_adjunto = serializers.FileField(required=False, allow_null=True)
    
    class Meta:
        model = SolicitudDocumento
        fields = [
            'tipo', 'titulo', 'descripcion', 'justificacion',
            'documento', 'prioridad', 'fecha_limite', 'archivo_adjunto'
        ]
    
    def validate_fecha_limite(self, value):
        """Valida la fecha límite"""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha límite debe ser futura"
            )
        return value


class SolicitudDocumentoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar solicitudes
    """
    
    class Meta:
        model = SolicitudDocumento
        fields = [
            'titulo', 'descripcion', 'justificacion', 'prioridad', 'fecha_limite'
        ]
    
    def validate_fecha_limite(self, value):
        """Valida la fecha límite"""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha límite debe ser futura"
            )
        return value


class AsignarSolicitudSerializer(serializers.Serializer):
    """
    Serializer para asignar solicitudes
    """
    
    asignado_a = serializers.CharField(max_length=50)
    comentarios = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ResponderSolicitudSerializer(serializers.Serializer):
    """
    Serializer para responder solicitudes
    """
    
    respuesta = serializers.CharField(max_length=2000)
    estado = serializers.ChoiceField(
        choices=[
            (EstadoSolicitud.APROBADO, 'Aprobado'),
            (EstadoSolicitud.RECHAZADO, 'Rechazado'),
            (EstadoSolicitud.COMPLETADO, 'Completado'),
        ]
    )


class FlujoDocumentoSerializer(BaseModelSerializer):
    """
    Serializer para el flujo de documentos
    """
    
    paso_display = serializers.CharField(source='get_paso_display', read_only=True)
    estado_anterior_display = serializers.CharField(
        source='get_estado_anterior_display', 
        read_only=True
    )
    estado_nuevo_display = serializers.CharField(
        source='get_estado_nuevo_display', 
        read_only=True
    )
    documento_titulo = serializers.CharField(source='documento.titulo', read_only=True)
    
    class Meta:
        model = FlujoDocumento
        fields = [
            'id', 'documento', 'documento_titulo', 'paso', 'paso_display',
            'usuario_id', 'detalle', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display', 'fecha_accion',
            'duracion_segundos', 'ip_address', 'datos_adicionales'
        ]


class AprobarDocumentoSerializer(serializers.Serializer):
    """
    Serializer para aprobar documentos
    """
    
    comentarios = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class RechazarDocumentoSerializer(serializers.Serializer):
    """
    Serializer para rechazar documentos
    """
    
    motivo = serializers.CharField(max_length=1000)


class FirmarDocumentoSerializer(serializers.Serializer):
    """
    Serializer para firmar documentos
    """
    
    firma_digital = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    comentarios = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class EstadisticasSerializer(serializers.Serializer):
    """
    Serializer para estadísticas del sistema
    """
    
    total = serializers.IntegerField()
    por_estado = serializers.DictField(child=serializers.IntegerField())
    por_tipo = serializers.DictField(child=serializers.IntegerField())
    publicos = serializers.IntegerField()
    confidenciales = serializers.IntegerField()
    vigentes = serializers.IntegerField()
    proximos_vencer = serializers.IntegerField()


class BusquedaSerializer(serializers.Serializer):
    """
    Serializer para parámetros de búsqueda
    """
    
    q = serializers.CharField(max_length=200, help_text="Término de búsqueda")
    tipo = serializers.ChoiceField(
        choices=TipoDocumento.CHOICES,
        required=False,
        help_text="Filtrar por tipo de documento"
    )
    estado = serializers.ChoiceField(
        choices=EstadoDocumento.CHOICES,
        required=False,
        help_text="Filtrar por estado"
    )
    autor_id = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Filtrar por autor"
    )
    categoria = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Filtrar por categoría"
    )
    publico = serializers.BooleanField(
        required=False,
        help_text="Filtrar por documentos públicos"
    )
    fecha_desde = serializers.DateField(
        required=False,
        help_text="Fecha de inicio (YYYY-MM-DD)"
    )
    fecha_hasta = serializers.DateField(
        required=False,
        help_text="Fecha de fin (YYYY-MM-DD)"
    )
    page = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="Número de página"
    )
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text="Elementos por página"
    )


class OpcionesSerializer(serializers.Serializer):
    """
    Serializer para opciones del sistema
    """
    
    tipos_documento = serializers.SerializerMethodField()
    estados_documento = serializers.SerializerMethodField()
    tipos_solicitud = serializers.SerializerMethodField()
    estados_solicitud = serializers.SerializerMethodField()
    prioridades = serializers.SerializerMethodField()
    tipos_archivo_permitidos = serializers.SerializerMethodField()
    tamano_maximo_archivo = serializers.SerializerMethodField()
    
    def get_tipos_documento(self, obj):
        """Tipos de documento disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TipoDocumento.CHOICES]
    
    def get_estados_documento(self, obj):
        """Estados de documento disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in EstadoDocumento.CHOICES]
    
    def get_tipos_solicitud(self, obj):
        """Tipos de solicitud disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TipoSolicitud.CHOICES]
    
    def get_estados_solicitud(self, obj):
        """Estados de solicitud disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in EstadoSolicitud.CHOICES]
    
    def get_prioridades(self, obj):
        """Prioridades disponibles"""
        return [
            {'value': 'BAJA', 'label': 'Baja'},
            {'value': 'MEDIA', 'label': 'Media'},
            {'value': 'ALTA', 'label': 'Alta'},
            {'value': 'URGENTE', 'label': 'Urgente'},
        ]
    
    def get_tipos_archivo_permitidos(self, obj):
        """Tipos de archivo permitidos"""
        from django.conf import settings
        return settings.ALLOWED_FILE_TYPES
    
    def get_tamano_maximo_archivo(self, obj):
        """Tamaño máximo de archivo en bytes"""
        from django.conf import settings
        return settings.MAX_FILE_SIZE