"""
Factory patterns para el servicio de documentos

Implementa el patrón Factory para generar números de seguimiento
únicos y otros elementos que requieren generación automática
"""
import uuid
import secrets
import string
from datetime import datetime
from typing import Optional
from django.utils import timezone
from django.db import models, transaction


class NumeroSeguimientoFactory:
    """
    Factory para generar números de seguimiento únicos
    
    Implementa el patrón Factory para crear números de seguimiento
    únicos para solicitudes de documentos
    """
    
    # Prefijos por tipo de solicitud
    PREFIJOS = {
        'CREACION': 'CRE',
        'MODIFICACION': 'MOD',
        'APROBACION': 'APR',
        'REVISION': 'REV',
        'PUBLICACION': 'PUB',
        'ARCHIVO': 'ARC',
        'ACCESO': 'ACC',
        'COPIA': 'COP',
        'OTRO': 'OTR'
    }
    
    @classmethod
    def generar(cls, tipo_solicitud: Optional[str] = None) -> str:
        """
        Genera un número de seguimiento único
        
        Args:
            tipo_solicitud: Tipo de solicitud para determinar el prefijo
            
        Returns:
            Número de seguimiento único
        """
        # Obtener prefijo
        prefijo = cls.PREFIJOS.get(tipo_solicitud, 'DOC')
        
        # Generar timestamp
        timestamp = timezone.now()
        year = timestamp.year
        month = timestamp.month
        day = timestamp.day
        
        # Generar código secuencial del día
        secuencial = cls._obtener_secuencial_dia(prefijo, timestamp)
        
        # Generar código aleatorio
        codigo_aleatorio = cls._generar_codigo_aleatorio()
        
        # Formato: PRE-YYYY-MM-DD-SSSS-RND
        numero = f"{prefijo}-{year}-{month:02d}-{day:02d}-{secuencial:04d}-{codigo_aleatorio}"
        
        return numero
    
    @classmethod
    def _obtener_secuencial_dia(cls, prefijo: str, timestamp: datetime) -> int:
        """
        Obtiene el número secuencial para el día actual
        
        Args:
            prefijo: Prefijo del tipo de solicitud
            timestamp: Timestamp actual
            
        Returns:
            Número secuencial del día
        """
        # Importar aquí para evitar importación circular
        from .models import SolicitudDocumento
        
        # Obtener fecha sin hora
        fecha = timestamp.date()
        
        # Buscar solicitudes del día con el mismo prefijo
        filtro_numero = f"{prefijo}-{fecha.year}-{fecha.month:02d}-{fecha.day:02d}-"
        
        count = SolicitudDocumento.objects.filter(
            numero_seguimiento__startswith=filtro_numero
        ).count()
        
        return count + 1
    
    @classmethod
    def _generar_codigo_aleatorio(cls, longitud: int = 4) -> str:
        """
        Genera un código aleatorio
        
        Args:
            longitud: Longitud del código
            
        Returns:
            Código aleatorio
        """
        caracteres = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(caracteres) for _ in range(longitud))
    
    @classmethod
    def validar_numero(cls, numero: str) -> bool:
        """
        Valida el formato de un número de seguimiento
        
        Args:
            numero: Número a validar
            
        Returns:
            True si el formato es válido
        """
        try:
            partes = numero.split('-')
            
            # Debe tener 6 partes: PRE-YYYY-MM-DD-SSSS-RND
            if len(partes) != 6:
                return False
            
            prefijo, year, month, day, secuencial, codigo = partes
            
            # Validar prefijo
            if prefijo not in cls.PREFIJOS.values() and prefijo != 'DOC':
                return False
            
            # Validar año (debe ser numérico y entre 2020-2100)
            year_int = int(year)
            if year_int < 2020 or year_int > 2100:
                return False
            
            # Validar mes
            month_int = int(month)
            if month_int < 1 or month_int > 12:
                return False
            
            # Validar día
            day_int = int(day)
            if day_int < 1 or day_int > 31:
                return False
            
            # Validar secuencial
            secuencial_int = int(secuencial)
            if secuencial_int < 1 or secuencial_int > 9999:
                return False
            
            # Validar código aleatorio
            if len(codigo) != 4:
                return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    @classmethod
    def extraer_informacion(cls, numero: str) -> dict:
        """
        Extrae información de un número de seguimiento
        
        Args:
            numero: Número de seguimiento
            
        Returns:
            Diccionario con la información extraída
        """
        if not cls.validar_numero(numero):
            return {}
        
        try:
            partes = numero.split('-')
            prefijo, year, month, day, secuencial, codigo = partes
            
            # Buscar tipo de solicitud por prefijo
            tipo_solicitud = None
            for tipo, pref in cls.PREFIJOS.items():
                if pref == prefijo:
                    tipo_solicitud = tipo
                    break
            
            return {
                'prefijo': prefijo,
                'tipo_solicitud': tipo_solicitud,
                'year': int(year),
                'month': int(month),
                'day': int(day),
                'secuencial': int(secuencial),
                'codigo_aleatorio': codigo,
                'fecha': f"{year}-{month}-{day}"
            }
            
        except (ValueError, IndexError):
            return {}


class CodigoDocumentoFactory:
    """
    Factory para generar códigos únicos de documentos
    
    Genera códigos únicos basados en el tipo de documento,
    fecha y secuencia
    """
    
    # Prefijos por tipo de documento
    PREFIJOS_TIPO = {
        'POLITICA': 'POL',
        'PROCEDIMIENTO': 'PRO',
        'INSTRUCTIVO': 'INS',
        'FORMATO': 'FOR',
        'MANUAL': 'MAN',
        'REGLAMENTO': 'REG',
        'ACTA': 'ACT',
        'INFORME': 'INF',
        'CIRCULAR': 'CIR',
        'MEMORANDO': 'MEM',
        'OFICIO': 'OFI',
        'RESOLUCION': 'RES',
        'CONTRATO': 'CON',
        'CONVENIO': 'CNV',
        'CERTIFICADO': 'CER',
        'OTRO': 'DOC'
    }
    
    @classmethod
    def generar(cls, tipo_documento: str, categoria: Optional[str] = None) -> str:
        """
        Genera un código único para el documento
        
        Args:
            tipo_documento: Tipo de documento
            categoria: Categoría del documento (opcional)
            
        Returns:
            Código único del documento
        """
        # Obtener prefijo del tipo
        prefijo_tipo = cls.PREFIJOS_TIPO.get(tipo_documento, 'DOC')
        
        # Obtener prefijo de categoría si existe
        prefijo_categoria = ''
        if categoria:
            prefijo_categoria = cls._generar_prefijo_categoria(categoria)
        
        # Obtener año actual
        year = timezone.now().year
        
        # Obtener secuencial
        secuencial = cls._obtener_secuencial(prefijo_tipo, prefijo_categoria, year)
        
        # Construir código
        if prefijo_categoria:
            codigo = f"{prefijo_tipo}-{prefijo_categoria}-{year}-{secuencial:04d}"
        else:
            codigo = f"{prefijo_tipo}-{year}-{secuencial:04d}"
        
        return codigo
    
    @classmethod
    def _generar_prefijo_categoria(cls, categoria: str) -> str:
        """
        Genera un prefijo de 2-3 letras basado en la categoría
        
        Args:
            categoria: Nombre de la categoría
            
        Returns:
            Prefijo de la categoría
        """
        # Limpiar y normalizar
        categoria = categoria.upper().strip()
        
        # Remover palabras comunes
        palabras_ignorar = ['DE', 'LA', 'EL', 'DEL', 'Y', 'EN', 'CON', 'POR', 'PARA']
        palabras = [p for p in categoria.split() if p not in palabras_ignorar]
        
        if not palabras:
            return ''
        
        # Generar prefijo
        if len(palabras) == 1:
            # Una palabra: primeras 3 letras
            return palabras[0][:3]
        elif len(palabras) == 2:
            # Dos palabras: primera letra de cada una + primera letra de la primera
            return palabras[0][:2] + palabras[1][:1]
        else:
            # Tres o más palabras: primera letra de las primeras tres
            return palabras[0][:1] + palabras[1][:1] + palabras[2][:1]
    
    @classmethod
    def _obtener_secuencial(
        cls, 
        prefijo_tipo: str, 
        prefijo_categoria: str, 
        year: int
    ) -> int:
        """
        Obtiene el número secuencial para el código
        
        Args:
            prefijo_tipo: Prefijo del tipo de documento
            prefijo_categoria: Prefijo de la categoría
            year: Año
            
        Returns:
            Número secuencial
        """
        # Importar aquí para evitar importación circular
        from .models import Documento
        
        # Construir patrón de búsqueda
        if prefijo_categoria:
            patron = f"{prefijo_tipo}-{prefijo_categoria}-{year}-"
        else:
            patron = f"{prefijo_tipo}-{year}-"
        
        # Contar documentos existentes
        count = Documento.objects.filter(
            codigo_documento__startswith=patron
        ).count()
        
        return count + 1


class VersionFactory:
    """
    Factory para generar números de versión
    
    Maneja la lógica de versionado de documentos
    """
    
    @classmethod
    def siguiente_version_menor(cls, version_actual: str) -> str:
        """
        Genera la siguiente versión menor
        
        Args:
            version_actual: Versión actual (ej: "1.0")
            
        Returns:
            Nueva versión menor (ej: "1.1")
        """
        try:
            from decimal import Decimal
            version_decimal = Decimal(version_actual)
            nueva_version = version_decimal + Decimal('0.1')
            return str(nueva_version)
        except Exception:
            return "1.1"
    
    @classmethod
    def siguiente_version_mayor(cls, version_actual: str) -> str:
        """
        Genera la siguiente versión mayor
        
        Args:
            version_actual: Versión actual (ej: "1.5")
            
        Returns:
            Nueva versión mayor (ej: "2.0")
        """
        try:
            from decimal import Decimal
            version_decimal = Decimal(version_actual)
            parte_entera = int(version_decimal)
            nueva_version = Decimal(str(parte_entera + 1) + '.0')
            return str(nueva_version)
        except Exception:
            return "2.0"
    
    @classmethod
    def es_version_mayor(cls, version: str) -> bool:
        """
        Verifica si una versión es mayor (x.0)
        
        Args:
            version: Versión a verificar
            
        Returns:
            True si es versión mayor
        """
        try:
            from decimal import Decimal
            version_decimal = Decimal(version)
            return version_decimal % 1 == 0
        except Exception:
            return False


class TokenAccesoFactory:
    """
    Factory para generar tokens de acceso temporal
    
    Genera tokens únicos para acceso temporal a documentos
    """
    
    @classmethod
    def generar_token(cls, documento_id: str, usuario_id: str, duracion_horas: int = 24) -> str:
        """
        Genera un token de acceso temporal
        
        Args:
            documento_id: ID del documento
            usuario_id: ID del usuario
            duracion_horas: Duración del token en horas
            
        Returns:
            Token de acceso
        """
        # Generar token base
        token_base = secrets.token_urlsafe(32)
        
        # Timestamp de expiración
        expiracion = timezone.now().timestamp() + (duracion_horas * 3600)
        
        # Crear hash de verificación
        import hashlib
        data = f"{documento_id}{usuario_id}{token_base}{expiracion}"
        verificacion = hashlib.sha256(data.encode()).hexdigest()[:8]
        
        # Construir token final
        token = f"{token_base}.{int(expiracion)}.{verificacion}"
        
        return token
    
    @classmethod
    def validar_token(cls, token: str, documento_id: str, usuario_id: str) -> bool:
        """
        Valida un token de acceso
        
        Args:
            token: Token a validar
            documento_id: ID del documento
            usuario_id: ID del usuario
            
        Returns:
            True si el token es válido
        """
        try:
            partes = token.split('.')
            if len(partes) != 3:
                return False
            
            token_base, timestamp_str, verificacion = partes
            timestamp = int(timestamp_str)
            
            # Verificar si no ha expirado
            if timezone.now().timestamp() > timestamp:
                return False
            
            # Verificar hash
            import hashlib
            data = f"{documento_id}{usuario_id}{token_base}{timestamp}"
            verificacion_esperada = hashlib.sha256(data.encode()).hexdigest()[:8]
            
            return verificacion == verificacion_esperada
            
        except (ValueError, IndexError):
            return False


class NotificacionFactory:
    """
    Factory para crear notificaciones
    
    Genera notificaciones estándar para diferentes eventos
    """
    
    PLANTILLAS = {
        'documento_creado': {
            'titulo': 'Documento creado: {documento_titulo}',
            'mensaje': 'Se ha creado un nuevo documento "{documento_titulo}" de tipo {documento_tipo}.',
            'tipo': 'info'
        },
        'documento_aprobado': {
            'titulo': 'Documento aprobado: {documento_titulo}',
            'mensaje': 'El documento "{documento_titulo}" ha sido aprobado por {aprobador_nombre}.',
            'tipo': 'success'
        },
        'documento_rechazado': {
            'titulo': 'Documento rechazado: {documento_titulo}',
            'mensaje': 'El documento "{documento_titulo}" ha sido rechazado. Motivo: {motivo}',
            'tipo': 'warning'
        },
        'solicitud_creada': {
            'titulo': 'Nueva solicitud: {solicitud_numero}',
            'mensaje': 'Se ha creado una nueva solicitud "{solicitud_titulo}" con número {solicitud_numero}.',
            'tipo': 'info'
        },
        'solicitud_asignada': {
            'titulo': 'Solicitud asignada: {solicitud_numero}',
            'mensaje': 'Se le ha asignado la solicitud "{solicitud_titulo}" con número {solicitud_numero}.',
            'tipo': 'info'
        },
    }
    
    @classmethod
    def crear_notificacion(
        cls, 
        tipo_evento: str, 
        destinatario_id: str, 
        datos: dict
    ) -> dict:
        """
        Crea una notificación basada en el tipo de evento
        
        Args:
            tipo_evento: Tipo de evento
            destinatario_id: ID del destinatario
            datos: Datos para completar la plantilla
            
        Returns:
            Diccionario con los datos de la notificación
        """
        plantilla = cls.PLANTILLAS.get(tipo_evento)
        if not plantilla:
            return {}
        
        try:
            titulo = plantilla['titulo'].format(**datos)
            mensaje = plantilla['mensaje'].format(**datos)
            
            return {
                'id': str(uuid.uuid4()),
                'destinatario_id': destinatario_id,
                'titulo': titulo,
                'mensaje': mensaje,
                'tipo': plantilla['tipo'],
                'fecha_creacion': timezone.now().isoformat(),
                'leida': False,
                'datos_adicionales': datos
            }
            
        except KeyError as e:
            # Si faltan datos para completar la plantilla
            return {
                'error': f'Faltan datos para la plantilla: {e}'
            }