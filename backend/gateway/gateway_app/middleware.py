"""
Middlewares para el API Gateway
- Rate limiting
- JWT validation
"""

import time
import json
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware para limitar la tasa de peticiones por IP
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', False)
        self.requests_per_minute = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 60)
        self.requests_per_hour = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_HOUR', 1000)
    
    def process_request(self, request):
        """
        Procesa cada petición entrante para aplicar rate limiting
        """
        if not self.enabled:
            return None
            
        # Obtener IP del cliente
        client_ip = self.get_client_ip(request)
        
        # Verificar límites
        if self.is_rate_limited(client_ip):
            return JsonResponse({
                'error': 'Too many requests',
                'message': f'Rate limit exceeded. Max {self.requests_per_minute} requests per minute.',
                'retry_after': 60
            }, status=429)
        
        # Incrementar contadores
        self.increment_counters(client_ip)
        
        return None
    
    def get_client_ip(self, request):
        """
        Obtiene la IP del cliente considerando proxies
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_cache_key(self, ip, time_window):
        """
        Genera clave de cache para el rate limiting
        """
        return f'rate_limit:{ip}:{time_window}'
    
    def is_rate_limited(self, ip):
        """
        Verifica si la IP ha excedido los límites
        """
        try:
            # Verificar límite por minuto
            minute_key = self.get_cache_key(ip, 'minute')
            minute_count = cache.get(minute_key, 0)
            
            if minute_count >= self.requests_per_minute:
                return True
            
            # Verificar límite por hora
            hour_key = self.get_cache_key(ip, 'hour')
            hour_count = cache.get(hour_key, 0)
            
            if hour_count >= self.requests_per_hour:
                return True
                
            return False
        except Exception:
            # Si hay error con cache, permitir la petición
            return False
    
    def increment_counters(self, ip):
        """
        Incrementa los contadores de peticiones
        """
        try:
            # Incrementar contador por minuto
            minute_key = self.get_cache_key(ip, 'minute')
            cache.set(minute_key, cache.get(minute_key, 0) + 1, 60)
            
            # Incrementar contador por hora
            hour_key = self.get_cache_key(ip, 'hour')
            cache.set(hour_key, cache.get(hour_key, 0) + 1, 3600)
        except Exception:
            # Si hay error con cache, continuar sin incrementar
            pass


class JWTValidationMiddleware(MiddlewareMixin):
    """
    Middleware para validar tokens JWT en endpoints protegidos
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.enabled = getattr(settings, 'JWT_VALIDATION_ENABLED', False)
        
        # Rutas que no requieren JWT
        self.excluded_paths = [
            '/health/',
            '/api/docs/',
            '/api/schema/',
            '/admin/',
            '/api/auth/login/',
            '/api/auth/register/',
        ]
    
    def process_request(self, request):
        """
        Procesa cada petición para validar JWT si es necesario
        """
        if not self.enabled:
            return None
            
        # Verificar si la ruta está excluida
        if self.is_excluded_path(request.path):
            return None
        
        # Obtener token del header
        token = self.get_token_from_request(request)
        
        if not token:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'JWT token is required for this endpoint'
            }, status=401)
        
        # Validar token
        if not self.validate_token(token):
            return JsonResponse({
                'error': 'Invalid token',
                'message': 'The provided JWT token is invalid or expired'
            }, status=401)
        
        return None
    
    def is_excluded_path(self, path):
        """
        Verifica si la ruta está excluida de validación JWT
        """
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return True
        return False
    
    def get_token_from_request(self, request):
        """
        Extrae el token JWT del header Authorization
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None
    
    def validate_token(self, token):
        """
        Valida el token JWT
        """
        try:
            UntypedToken(token)
            return True
        except (InvalidToken, TokenError):
            return False