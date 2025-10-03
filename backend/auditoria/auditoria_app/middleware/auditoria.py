"""
Middleware de auditoría para registro automático de actividades
"""

from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import time
import json
import logging
from typing import Dict, Any, Optional
import traceback

from ..services import AuditoriaService

logger = logging.getLogger('audit')


class AuditoriaMiddleware(MiddlewareMixin):
    """
    Middleware para registrar automáticamente todas las actividades del sistema
    
    Registra:
    - Todas las requests HTTP
    - Respuestas y códigos de estado
    - Duración de las operaciones
    - Errores y excepciones
    - Información del usuario y sesión
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.auditoria_service = AuditoriaService()
        self.config = getattr(settings, 'AUDITORIA_CONFIG', {})
        self.enabled = self.config.get('ENABLE_MIDDLEWARE', True)
        self.log_anonymous = self.config.get('LOG_ANONYMOUS_USERS', False)
        self.exclude_paths = self.config.get('EXCLUDE_PATHS', [])
        self.exclude_methods = self.config.get('EXCLUDE_METHODS', ['OPTIONS'])
        self.log_request_body = self.config.get('LOG_REQUEST_BODY', True)
        self.log_response_body = self.config.get('LOG_RESPONSE_BODY', False)
        self.max_body_length = self.config.get('MAX_BODY_LENGTH', 10000)
    
    def process_request(self, request):
        """
        Procesar request entrante
        """
        if not self.enabled:
            return None
        
        # Marcar inicio del tiempo
        request._audit_start_time = time.time()
        
        # Verificar si debe ser excluida
        if self._should_exclude_request(request):
            request._audit_excluded = True
            return None
        
        request._audit_excluded = False
        
        # Extraer información de la request
        request._audit_data = self._extract_request_data(request)
        
        return None
    
    def process_response(self, request, response):
        """
        Procesar response saliente
        """
        if not self.enabled or getattr(request, '_audit_excluded', True):
            return response
        
        try:
            # Calcular duración
            start_time = getattr(request, '_audit_start_time', time.time())
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Obtener datos de la request
            request_data = getattr(request, '_audit_data', {})
            
            # Determinar acción basada en método y URL
            accion = self._determine_action(request, response)
            recurso = self._determine_resource(request)
            
            # Preparar detalles
            detalle = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'content_type': response.get('Content-Type', ''),
            }
            
            # Agregar datos del request body si está habilitado
            if self.log_request_body and hasattr(request, 'body'):
                try:
                    body = request.body.decode('utf-8')
                    if len(body) <= self.max_body_length:
                        detalle['request_body'] = body
                    else:
                        detalle['request_body'] = body[:self.max_body_length] + '... (truncated)'
                except:
                    detalle['request_body'] = '<binary or unreadable data>'
            
            # Agregar query parameters
            if request.GET:
                detalle['query_params'] = dict(request.GET)
            
            # Determinar si fue exitoso
            exito = 200 <= response.status_code < 400
            
            # Determinar usuario
            usuario_id = None
            usuario_email = None
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                usuario_id = request.user.id
                usuario_email = getattr(request.user, 'email', None)
            elif not self.log_anonymous:
                # No registrar usuarios anónimos si está deshabilitado
                return response
            
            # Registrar actividad
            self.auditoria_service.registrar_actividad(
                usuario_id=usuario_id,
                usuario_email=usuario_email,
                accion=accion,
                recurso=recurso,
                detalle=detalle,
                request_data=request_data,
                duracion_ms=duration_ms,
                codigo_estado=response.status_code,
                exito=exito,
                microservicio=self._get_microservice_name(request)
            )
            
        except Exception as e:
            # No fallar la request por errores en auditoría
            logger.error(f"Error en middleware de auditoría: {str(e)}")
            logger.error(traceback.format_exc())
        
        return response
    
    def process_exception(self, request, exception):
        """
        Procesar excepciones
        """
        if not self.enabled or getattr(request, '_audit_excluded', True):
            return None
        
        try:
            # Calcular duración hasta la excepción
            start_time = getattr(request, '_audit_start_time', time.time())
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Obtener datos de la request
            request_data = getattr(request, '_audit_data', {})
            
            # Preparar detalles de la excepción
            detalle = {
                'method': request.method,
                'path': request.path,
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception),
                'duration_ms': duration_ms,
                'traceback': traceback.format_exc()
            }
            
            # Determinar usuario
            usuario_id = None
            usuario_email = None
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                usuario_id = request.user.id
                usuario_email = getattr(request.user, 'email', None)
            
            # Registrar excepción
            self.auditoria_service.registrar_error(
                usuario_id=usuario_id,
                recurso=self._determine_resource(request),
                mensaje_error=str(exception),
                detalle=detalle,
                usuario_email=usuario_email,
                request_data=request_data,
                duracion_ms=duration_ms,
                microservicio=self._get_microservice_name(request)
            )
            
        except Exception as e:
            logger.error(f"Error al registrar excepción en auditoría: {str(e)}")
        
        return None
    
    def _should_exclude_request(self, request) -> bool:
        """
        Determinar si la request debe ser excluida
        """
        # Excluir por método
        if request.method in self.exclude_methods:
            return True
        
        # Excluir por path
        path = request.path
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        
        # Excluir usuarios anónimos si está configurado
        if not self.log_anonymous and (not hasattr(request, 'user') or not request.user.is_authenticated):
            return True
        
        return False
    
    def _extract_request_data(self, request) -> Dict[str, Any]:
        """
        Extraer datos relevantes de la request
        """
        data = {
            'method': request.method,
            'url': request.build_absolute_uri(),
            'path': request.path,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_key': getattr(request.session, 'session_key', None),
        }
        
        # Agregar headers relevantes
        relevant_headers = [
            'HTTP_REFERER', 'HTTP_ACCEPT', 'HTTP_ACCEPT_LANGUAGE',
            'HTTP_ACCEPT_ENCODING', 'HTTP_CONNECTION', 'HTTP_X_FORWARDED_FOR'
        ]
        
        headers = {}
        for header in relevant_headers:
            if header in request.META:
                headers[header] = request.META[header]
        
        if headers:
            data['headers'] = headers
        
        return data
    
    def _get_client_ip(self, request) -> str:
        """
        Obtener IP real del cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _determine_action(self, request, response) -> str:
        """
        Determinar acción basada en método HTTP y respuesta
        """
        method = request.method.upper()
        status = response.status_code
        
        # Mapeo básico HTTP -> Acción
        method_mapping = {
            'GET': 'READ',
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE',
            'HEAD': 'READ',
            'OPTIONS': 'OTHER'
        }
        
        base_action = method_mapping.get(method, 'OTHER')
        
        # Ajustar según código de estado
        if status >= 400:
            if status == 401:
                return 'ACCESS_DENIED'
            elif status == 403:
                return 'ACCESS_DENIED'
            elif status == 404:
                return 'READ'  # Intento de lectura de recurso no encontrado
            else:
                return 'ERROR'
        
        # Detectar acciones específicas por URL
        path = request.path.lower()
        if '/login' in path or '/signin' in path:
            return 'LOGIN'
        elif '/logout' in path or '/signout' in path:
            return 'LOGOUT'
        elif '/upload' in path:
            return 'UPLOAD'
        elif '/download' in path:
            return 'DOWNLOAD'
        elif '/export' in path:
            return 'EXPORT'
        elif '/import' in path:
            return 'IMPORT'
        
        return base_action
    
    def _determine_resource(self, request) -> str:
        """
        Determinar recurso basado en la URL
        """
        path = request.path.lower()
        
        # Mapeo de paths a recursos
        resource_mapping = {
            '/api/auth/': 'AUTH',
            '/api/users/': 'USERS',
            '/api/profiles/': 'USER_PROFILE',
            '/api/documents/': 'DOCUMENTS',
            '/api/payments/': 'PAYMENTS',
            '/api/attendance/': 'ATTENDANCE',
            '/api/reports/': 'REPORTS',
            '/api/audit/': 'AUDIT',
            '/admin/': 'SYSTEM',
            '/api/': 'API',
        }
        
        for path_prefix, resource in resource_mapping.items():
            if path.startswith(path_prefix):
                return resource
        
        # Detectar por microservicio
        if ':3001' in request.get_host():  # Auth
            return 'AUTH'
        elif ':3002' in request.get_host():  # Users
            return 'USERS'
        elif ':3003' in request.get_host():  # Attendance
            return 'ATTENDANCE'
        elif ':3004' in request.get_host():  # Payments
            return 'PAYMENTS'
        elif ':3005' in request.get_host():  # Documents
            return 'DOCUMENTS'
        elif ':3006' in request.get_host():  # Reports
            return 'REPORTS'
        elif ':3007' in request.get_host():  # Audit
            return 'AUDIT'
        
        return 'OTHER'
    
    def _get_microservice_name(self, request) -> str:
        """
        Determinar nombre del microservicio
        """
        host = request.get_host()
        
        if ':3001' in host:
            return 'AUTH'
        elif ':3002' in host:
            return 'USERS'
        elif ':3003' in host:
            return 'ATTENDANCE'
        elif ':3004' in host:
            return 'PAYMENTS'
        elif ':3005' in host:
            return 'DOCUMENTS'
        elif ':3006' in host:
            return 'REPORTS'
        elif ':3007' in host:
            return 'AUDIT'
        else:
            return 'UNKNOWN'


class AuditoriaAPIMiddleware(MiddlewareMixin):
    """
    Middleware especializado para APIs que registra operaciones CRUD
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.auditoria_service = AuditoriaService()
    
    def process_response(self, request, response):
        """
        Procesar respuestas de API para registrar operaciones CRUD
        """
        # Solo procesar APIs
        if not request.path.startswith('/api/'):
            return response
        
        # Solo usuarios autenticados
        if not (hasattr(request, 'user') and request.user.is_authenticated):
            return response
        
        try:
            # Extraer ID del recurso de la URL si existe
            recurso_id = self._extract_resource_id(request.path)
            
            # Registrar operación CRUD
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and 200 <= response.status_code < 300:
                self.auditoria_service.registrar_operacion_crud(
                    usuario_id=request.user.id,
                    accion=self._map_method_to_crud(request.method),
                    recurso=self._determine_api_resource(request.path),
                    recurso_id=recurso_id,
                    detalle={
                        'api_endpoint': request.path,
                        'method': request.method,
                        'status_code': response.status_code
                    },
                    exito=True
                )
        
        except Exception as e:
            logger.error(f"Error en middleware de API auditoría: {str(e)}")
        
        return response
    
    def _extract_resource_id(self, path: str) -> Optional[str]:
        """
        Extraer ID del recurso de la URL
        """
        import re
        # Buscar patrones como /api/resource/123/ o /api/resource/uuid/
        pattern = r'/api/[^/]+/([a-zA-Z0-9\-]+)/?'
        match = re.search(pattern, path)
        return match.group(1) if match else None
    
    def _map_method_to_crud(self, method: str) -> str:
        """
        Mapear método HTTP a operación CRUD
        """
        mapping = {
            'POST': 'CREATE',
            'GET': 'READ',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE'
        }
        return mapping.get(method.upper(), 'OTHER')
    
    def _determine_api_resource(self, path: str) -> str:
        """
        Determinar recurso de API basado en la URL
        """
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'api':
            resource_name = path_parts[1].upper()
            
            # Mapear nombres comunes
            resource_mapping = {
                'USERS': 'USERS',
                'PROFILES': 'USER_PROFILE',
                'DOCUMENTS': 'DOCUMENTS',
                'PAYMENTS': 'PAYMENTS',
                'ATTENDANCE': 'ATTENDANCE',
                'REPORTS': 'REPORTS',
                'AUDIT': 'AUDIT',
                'AUTH': 'AUTH'
            }
            
            return resource_mapping.get(resource_name, 'API')
        
        return 'API'