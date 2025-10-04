"""
Middleware para proxy de requests a microservicios
"""

import json
import time
import logging
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
import requests

from ..services import gateway_service, circuit_breakers, RequestLogger

logger = logging.getLogger('gateway')


class ProxyMiddleware(MiddlewareMixin):
    """
    Middleware que proxea requests a microservicios apropiados
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.gateway_service = gateway_service
        self.circuit_breakers = circuit_breakers
        self.config = getattr(settings, 'GATEWAY_CONFIG', {})
        self.enabled = self.config.get('ENABLE_PROXY', True)
        
        # Rutas que no deben ser proxeadas
        self.excluded_paths = [
            '/admin/',
            '/api/docs/',
            '/api/schema/',
            '/health/',
            '/api/gateway/',
            '/static/',
            '/media/',
        ]
    
    def process_request(self, request):
        """
        Procesar request entrante
        """
        if not self.enabled:
            return None
        
        path = request.path
        
        # Verificar si la ruta debe ser excluida
        if self._should_exclude(path):
            return None
        
        # Verificar si es una ruta de API que debe ser proxeada
        if not path.startswith('/api/'):
            return None
        
        # Extraer servicio de la ruta
        service_name = self._extract_service_name(path)
        if not service_name:
            return JsonResponse(
                {'error': 'Invalid API route', 'path': path}, 
                status=400
            )
        
        # Verificar si el servicio existe
        if service_name not in self.gateway_service.clients:
            return JsonResponse(
                {'error': f'Unknown service: {service_name}'}, 
                status=404
            )
        
        # Verificar circuit breaker
        circuit_breaker = self.circuit_breakers.get(service_name)
        if circuit_breaker and not circuit_breaker.can_request():
            return JsonResponse(
                {'error': f'Service {service_name} is temporarily unavailable'}, 
                status=503
            )
        
        # Proxear request
        return self._proxy_request(request, service_name)
    
    def _should_exclude(self, path: str) -> bool:
        """
        Verificar si la ruta debe ser excluida del proxy
        """
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return True
        return False
    
    def _extract_service_name(self, path: str) -> str:
        """
        Extraer nombre del servicio de la ruta
        Ejemplo: /api/users/profile/ -> users
        """
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] == 'api':
            service_name = parts[1]
            
            # Mapear nombres de servicios
            service_mapping = {
                'auth': 'auth',
                'users': 'users', 
                'attendance': 'attendance',
                'payments': 'payments',
                'documents': 'documents',
                'reports': 'reports',
                'audit': 'audit',
            }
            
            return service_mapping.get(service_name)
        
        return None
    
    def _proxy_request(self, request, service_name: str):
        """
        Proxear request al microservicio
        """
        start_time = time.time()
        
        try:
            # Preparar datos del request
            method = request.method
            path = request.path
            headers = self._prepare_headers(request)
            
            # Preparar parámetros para el request
            kwargs = {}
            
            # Query parameters
            if request.GET:
                kwargs['params'] = dict(request.GET)
            
            # Body data
            if request.body:
                try:
                    if request.content_type == 'application/json':
                        kwargs['json'] = json.loads(request.body)
                    else:
                        kwargs['data'] = request.body
                except (json.JSONDecodeError, UnicodeDecodeError):
                    kwargs['data'] = request.body
            
            # Files
            if hasattr(request, 'FILES') and request.FILES:
                kwargs['files'] = {
                    name: (file.name, file.read(), file.content_type)
                    for name, file in request.FILES.items()
                }
            
            # Hacer request al microservicio
            response = self.gateway_service.proxy_request(
                service_name, method, path, headers, **kwargs
            )
            
            # Calcular tiempo de respuesta
            response_time = time.time() - start_time
            
            # Registrar éxito en circuit breaker
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker:
                circuit_breaker.record_success()
            
            # Log request
            RequestLogger.log_request(
                service_name, method, path, response.status_code, 
                response_time, getattr(request, 'user_id', None)
            )
            
            # Crear response de Django
            django_response = HttpResponse(
                content=response.content,
                status=response.status_code,
                content_type=response.headers.get('content-type', 'application/json')
            )
            
            # Copiar headers relevantes
            for header, value in response.headers.items():
                if header.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                    django_response[header] = value
            
            return django_response
            
        except requests.exceptions.RequestException as e:
            # Registrar error en circuit breaker
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker:
                circuit_breaker.record_failure()
            
            # Log error
            RequestLogger.log_error(service_name, method, path, str(e))
            
            # Determinar código de error
            if isinstance(e, requests.exceptions.Timeout):
                status_code = 504  # Gateway Timeout
                error_message = f'Service {service_name} timeout'
            elif isinstance(e, requests.exceptions.ConnectionError):
                status_code = 503  # Service Unavailable
                error_message = f'Service {service_name} unavailable'
            else:
                status_code = 502  # Bad Gateway
                error_message = f'Error connecting to {service_name}'
            
            return JsonResponse(
                {
                    'error': error_message,
                    'service': service_name,
                    'details': str(e)
                },
                status=status_code
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in proxy: {str(e)}")
            return JsonResponse(
                {'error': 'Internal gateway error'},
                status=500
            )
    
    def _prepare_headers(self, request) -> dict:
        """
        Preparar headers para el request proxeado
        """
        headers = {}
        
        # Headers importantes a propagar
        important_headers = [
            'authorization',
            'content-type',
            'accept',
            'user-agent',
            'x-forwarded-for',
            'x-real-ip',
        ]
        
        for header in important_headers:
            value = request.META.get(f'HTTP_{header.upper().replace("-", "_")}')
            if value:
                headers[header] = value
        
        # Agregar headers de contexto del gateway
        headers['X-Gateway-Service'] = 'pontificia-gateway'
        headers['X-Forwarded-Host'] = request.get_host()
        headers['X-Forwarded-Proto'] = request.scheme
        
        # IP del cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            headers['X-Forwarded-For'] = x_forwarded_for
        else:
            headers['X-Forwarded-For'] = request.META.get('REMOTE_ADDR', '')
        
        return headers


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware para rate limiting
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.enabled = getattr(settings, 'RATELIMIT_ENABLE', True)
        self.rate_limits = getattr(settings, 'RATE_LIMITS', {})
    
    def process_request(self, request):
        """
        Aplicar rate limiting
        """
        if not self.enabled:
            return None
        
        # Determinar rate limit basado en la ruta
        rate_limit = self._get_rate_limit(request.path)
        if not rate_limit:
            return None
        
        # Obtener clave para rate limiting
        key = self._get_rate_limit_key(request)
        
        try:
            # Aplicar rate limit usando decorator
            @ratelimit(key=key, rate=rate_limit, method='ALL')
            def dummy_view(request):
                return None
            
            dummy_view(request)
            return None
            
        except Ratelimited:
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'limit': rate_limit,
                    'retry_after': 60
                },
                status=429
            )
    
    def _get_rate_limit(self, path: str) -> str:
        """
        Obtener rate limit para una ruta específica
        """
        if '/auth/' in path:
            return self.rate_limits.get('auth', self.rate_limits.get('default'))
        elif '/upload' in path:
            return self.rate_limits.get('upload', self.rate_limits.get('default'))
        elif '/download' in path:
            return self.rate_limits.get('download', self.rate_limits.get('default'))
        elif '/reports/' in path:
            return self.rate_limits.get('reports', self.rate_limits.get('default'))
        else:
            return self.rate_limits.get('default')
    
    def _get_rate_limit_key(self, request) -> str:
        """
        Obtener clave para rate limiting (IP o usuario)
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user_{request.user.id}"
        else:
            # Usar IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            return f"ip_{ip}"