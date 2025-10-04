"""
Funciones utilitarias para el servicio de documentos

Contiene funciones auxiliares y utilidades comunes
utilizadas en diferentes partes del sistema
"""
import os
import mimetypes
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from django.http import HttpRequest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from datetime import datetime, timedelta
from decimal import Decimal


def get_client_ip(request: HttpRequest) -> str:
    """
    Obtiene la dirección IP del cliente
    
    Args:
        request: Objeto HttpRequest de Django
        
    Returns:
        Dirección IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    
    return ip


def get_user_agent(request: HttpRequest) -> str:
    """
    Obtiene el User-Agent del cliente
    
    Args:
        request: Objeto HttpRequest de Django
        
    Returns:
        User-Agent del cliente
    """
    return request.META.get('HTTP_USER_AGENT', '')


def validate_file_type(file: UploadedFile) -> bool:
    """
    Valida el tipo de archivo
    
    Args:
        file: Archivo subido
        
    Returns:
        True si el tipo es válido
    """
    if not file or not file.name:
        return False
    
    # Obtener extensión
    extension = file.name.split('.')[-1].lower()
    
    # Verificar contra lista de tipos permitidos
    allowed_types = getattr(settings, 'ALLOWED_FILE_TYPES', [])
    return extension in allowed_types


def validate_file_size(file: UploadedFile) -> bool:
    """
    Valida el tamaño del archivo
    
    Args:
        file: Archivo subido
        
    Returns:
        True si el tamaño es válido
    """
    if not file:
        return False
    
    max_size = getattr(settings, 'MAX_FILE_SIZE', 50 * 1024 * 1024)  # 50MB por defecto
    return file.size <= max_size


def get_file_mime_type(file_path: str) -> str:
    """
    Obtiene el tipo MIME de un archivo
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Tipo MIME del archivo
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'


def calculate_file_hash(file: UploadedFile) -> str:
    """
    Calcula el hash SHA-256 de un archivo
    
    Args:
        file: Archivo subido
        
    Returns:
        Hash SHA-256 del archivo
    """
    hash_sha256 = hashlib.sha256()
    
    try:
        # Leer archivo en chunks para archivos grandes
        for chunk in file.chunks():
            hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    except Exception:
        return ''


def format_file_size(size_bytes: int) -> str:
    """
    Formatea el tamaño de archivo en formato legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        Tamaño formateado (ej: "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def generate_unique_filename(original_filename: str) -> str:
    """
    Genera un nombre único para un archivo
    
    Args:
        original_filename: Nombre original del archivo
        
    Returns:
        Nombre único del archivo
    """
    if not original_filename:
        return f"{secrets.token_hex(16)}.bin"
    
    # Separar nombre y extensión
    name, ext = os.path.splitext(original_filename)
    
    # Generar token único
    unique_token = secrets.token_hex(8)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{name}_{timestamp}_{unique_token}{ext}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres peligrosos
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        Nombre sanitizado
    """
    if not filename:
        return "archivo"
    
    # Caracteres peligrosos a remover
    dangerous_chars = '<>:"/\\|?*'
    
    # Reemplazar caracteres peligrosos
    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remover espacios múltiples y al inicio/final
    sanitized = ' '.join(sanitized.split())
    
    # Límite de longitud
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized or "archivo"


def parse_version_number(version_str: str) -> Decimal:
    """
    Parsea un número de versión a Decimal
    
    Args:
        version_str: Cadena de versión
        
    Returns:
        Número de versión como Decimal
    """
    try:
        return Decimal(str(version_str))
    except Exception:
        return Decimal('1.0')


def increment_version(current_version: str, major: bool = False) -> str:
    """
    Incrementa un número de versión
    
    Args:
        current_version: Versión actual
        major: Si es incremento mayor
        
    Returns:
        Nueva versión
    """
    try:
        version_decimal = Decimal(current_version)
        
        if major:
            # Incremento mayor: 1.5 -> 2.0
            integer_part = int(version_decimal)
            return str(Decimal(integer_part + 1))
        else:
            # Incremento menor: 1.0 -> 1.1
            return str(version_decimal + Decimal('0.1'))
    except Exception:
        return "1.1" if not major else "2.0"


def validate_documento_data(data: Dict[str, Any]) -> List[str]:
    """
    Valida los datos de un documento
    
    Args:
        data: Datos del documento
        
    Returns:
        Lista de errores de validación
    """
    errors = []
    
    # Validar título
    titulo = data.get('titulo', '').strip()
    if not titulo:
        errors.append("El título es requerido")
    elif len(titulo) > 200:
        errors.append("El título no puede exceder 200 caracteres")
    
    # Validar tipo
    tipo = data.get('tipo')
    if not tipo:
        errors.append("El tipo de documento es requerido")
    
    # Validar fechas
    fecha_vigencia = data.get('fecha_vigencia')
    fecha_vencimiento = data.get('fecha_vencimiento')
    
    if fecha_vigencia and fecha_vencimiento:
        if fecha_vigencia >= fecha_vencimiento:
            errors.append("La fecha de vigencia debe ser anterior a la fecha de vencimiento")
    
    return errors


def validate_solicitud_data(data: Dict[str, Any]) -> List[str]:
    """
    Valida los datos de una solicitud
    
    Args:
        data: Datos de la solicitud
        
    Returns:
        Lista de errores de validación
    """
    errors = []
    
    # Validar título
    titulo = data.get('titulo', '').strip()
    if not titulo:
        errors.append("El título es requerido")
    elif len(titulo) > 200:
        errors.append("El título no puede exceder 200 caracteres")
    
    # Validar descripción
    descripcion = data.get('descripcion', '').strip()
    if not descripcion:
        errors.append("La descripción es requerida")
    
    # Validar tipo
    tipo = data.get('tipo')
    if not tipo:
        errors.append("El tipo de solicitud es requerido")
    
    return errors


def create_pagination_metadata(
    total: int,
    page: int,
    page_size: int,
    max_pages: int = None
) -> Dict[str, Any]:
    """
    Crea metadatos de paginación
    
    Args:
        total: Total de elementos
        page: Página actual
        page_size: Tamaño de página
        max_pages: Máximo número de páginas
        
    Returns:
        Diccionario con metadatos de paginación
    """
    import math
    
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    
    if max_pages and total_pages > max_pages:
        total_pages = max_pages
    
    has_next = page < total_pages
    has_previous = page > 1
    
    return {
        'total': total,
        'pages': total_pages,
        'current_page': page,
        'page_size': page_size,
        'has_next': has_next,
        'has_previous': has_previous,
        'next_page': page + 1 if has_next else None,
        'previous_page': page - 1 if has_previous else None
    }


def clean_search_term(term: str) -> str:
    """
    Limpia un término de búsqueda
    
    Args:
        term: Término de búsqueda
        
    Returns:
        Término limpio
    """
    if not term:
        return ""
    
    # Remover caracteres especiales peligrosos
    cleaned = term.strip()
    
    # Remover caracteres de control
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32)
    
    # Límite de longitud
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    
    return cleaned


def build_filters_from_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construye filtros desde parámetros de consulta
    
    Args:
        params: Parámetros de consulta
        
    Returns:
        Diccionario de filtros
    """
    filters = {}
    
    # Filtros de texto
    text_filters = ['tipo', 'estado', 'autor_id', 'categoria', 'busqueda']
    for key in text_filters:
        value = params.get(key)
        if value and str(value).strip():
            filters[key] = str(value).strip()
    
    # Filtros booleanos
    bool_filters = ['publico', 'confidencial', 'vigente']
    for key in bool_filters:
        value = params.get(key)
        if value is not None:
            if isinstance(value, str):
                filters[key] = value.lower() in ['true', '1', 'yes', 'on']
            else:
                filters[key] = bool(value)
    
    # Filtros de fecha
    date_filters = ['fecha_desde', 'fecha_hasta']
    for key in date_filters:
        value = params.get(key)
        if value:
            try:
                if isinstance(value, str):
                    from datetime import datetime
                    filters[key] = datetime.strptime(value, '%Y-%m-%d').date()
                else:
                    filters[key] = value
            except ValueError:
                pass  # Ignorar fechas inválidas
    
    return filters


def generate_document_code(tipo: str, categoria: str = "", year: int = None) -> str:
    """
    Genera un código de documento
    
    Args:
        tipo: Tipo de documento
        categoria: Categoría del documento
        year: Año (por defecto el actual)
        
    Returns:
        Código generado
    """
    from datetime import datetime
    
    if not year:
        year = datetime.now().year
    
    # Prefijo del tipo
    tipo_prefix = tipo[:3].upper() if tipo else 'DOC'
    
    # Prefijo de categoría (opcional)
    cat_prefix = ""
    if categoria:
        cat_prefix = "-" + categoria.upper()[:3]
    
    # Generar número secuencial (simulado)
    import random
    secuencial = random.randint(1, 9999)
    
    return f"{tipo_prefix}{cat_prefix}-{year}-{secuencial:04d}"


def extract_file_metadata(file: UploadedFile) -> Dict[str, Any]:
    """
    Extrae metadatos de un archivo
    
    Args:
        file: Archivo subido
        
    Returns:
        Diccionario con metadatos
    """
    metadata = {
        'name': file.name,
        'size': file.size,
        'content_type': file.content_type,
        'mime_type': get_file_mime_type(file.name) if file.name else '',
        'extension': file.name.split('.')[-1].lower() if file.name and '.' in file.name else '',
        'hash': calculate_file_hash(file),
        'size_formatted': format_file_size(file.size)
    }
    
    return metadata


def format_datetime_for_display(dt: datetime) -> str:
    """
    Formatea una fecha/hora para mostrar
    
    Args:
        dt: Objeto datetime
        
    Returns:
        Fecha formateada
    """
    if not dt:
        return ""
    
    return dt.strftime("%d/%m/%Y %H:%M")


def format_date_for_display(date_obj) -> str:
    """
    Formatea una fecha para mostrar
    
    Args:
        date_obj: Objeto date
        
    Returns:
        Fecha formateada
    """
    if not date_obj:
        return ""
    
    return date_obj.strftime("%d/%m/%Y")


def calculate_time_elapsed(start_time: datetime) -> Dict[str, int]:
    """
    Calcula el tiempo transcurrido desde una fecha
    
    Args:
        start_time: Fecha de inicio
        
    Returns:
        Diccionario con el tiempo transcurrido
    """
    if not start_time:
        return {'days': 0, 'hours': 0, 'minutes': 0}
    
    now = datetime.now(start_time.tzinfo) if start_time.tzinfo else datetime.now()
    delta = now - start_time
    
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'total_hours': int(delta.total_seconds() / 3600)
    }


def is_file_expired(file_date: datetime, expiry_days: int = 365) -> bool:
    """
    Verifica si un archivo ha expirado
    
    Args:
        file_date: Fecha del archivo
        expiry_days: Días para expiración
        
    Returns:
        True si ha expirado
    """
    if not file_date:
        return False
    
    expiry_date = file_date + timedelta(days=expiry_days)
    return datetime.now(file_date.tzinfo) > expiry_date