"""
Middleware para validación JWT
"""

import jwt
import logging
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger('gateway')


class JWTValidationMiddleware(MiddlewareMixin):
    """
    Middleware para validar JWT tokens en el gateway
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.config = getattr(settings, 'GATEWAY_CONFIG', {})
        self.enabled = self.config.get('ENABLE_JWT_VALIDATION', True)
        
        # Rutas que no requieren autenticación
        self.excluded_paths = [
            '/',  # Ruta raíz
            '/admin/',
            '/docs/',
            '/api/docs/',
            '/api/redoc/',
            '/api/schema/',
            '/health/',
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/refresh/',
            '/api/gateway/health/',
            '/api/gateway/info/',
            '/test/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        # Rutas que son opcionales (pueden tener o no token)
        self.optional_auth_paths = [
            '/api/auth/verify/',
            '/api/gateway/',
        ]
    
    def process_request(self, request):
        """
        Validar JWT token en request
        """
        if not self.enabled:
            return None
        
        path = request.path
        
        # Verificar si la ruta está excluida
        if self._should_exclude(path):
            return None
        
        # Obtener token del header
        token = self._extract_token(request)
        
        # Si no hay token y la ruta requiere autenticación
        if not token:
            if self._is_optional_auth(path):
                request.user = AnonymousUser()
                return None
            else:
                return JsonResponse(
                    {'error': 'Authentication required', 'code': 'MISSING_TOKEN'},
                    status=401
                )
        
        # Validar token
        validation_result = self._validate_token(token)
        
        if not validation_result['valid']:
            return JsonResponse(
                {
                    'error': 'Invalid token',
                    'code': validation_result['error_code'],
                    'details': validation_result['error_message']
                },
                status=401
            )
        
        # Agregar información del usuario al request
        request.user_id = validation_result['user_id']
        request.user_email = validation_result.get('email')
        request.token_payload = validation_result['payload']
        
        # Agregar header con user_id para microservicios
        if hasattr(request, 'META'):
            request.META['HTTP_X_USER_ID'] = str(validation_result['user_id'])
            if validation_result.get('email'):
                request.META['HTTP_X_USER_EMAIL'] = validation_result['email']
        
        return None
    
    def _should_exclude(self, path: str) -> bool:
        """
        Verificar si la ruta debe ser excluida de validación JWT
        """
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _is_optional_auth(self, path: str) -> bool:
        """
        Verificar si la ruta tiene autenticación opcional
        """
        return any(path.startswith(optional) for optional in self.optional_auth_paths)
    
    def _extract_token(self, request) -> str:
        """
        Extraer token JWT del header Authorization
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remover "Bearer "
        
        return None
    
    def _validate_token(self, token: str) -> dict:
        """
        Validar token JWT
        """
        try:
            # Usar el validador de SimpleJWT
            access_token = AccessToken(token)
            payload = access_token.payload
            
            return {
                'valid': True,
                'user_id': payload.get('user_id'),
                'email': payload.get('email'),
                'payload': payload,
                'error_code': None,
                'error_message': None
            }
            
        except TokenError as e:
            error_code = 'INVALID_TOKEN'
            error_message = str(e)
            
            if 'expired' in str(e).lower():
                error_code = 'TOKEN_EXPIRED'
            elif 'invalid' in str(e).lower():
                error_code = 'TOKEN_INVALID'
            
            return {
                'valid': False,
                'user_id': None,
                'email': None,
                'payload': None,
                'error_code': error_code,
                'error_message': error_message
            }
            
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return {
                'valid': False,
                'user_id': None,
                'email': None,
                'payload': None,
                'error_code': 'VALIDATION_ERROR',
                'error_message': 'Token validation failed'
            }
    
    def _validate_token_manual(self, token: str) -> dict:
        """
        Validación manual de JWT (fallback)
        """
        try:
            # Decodificar token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Verificar claims requeridos
            required_claims = ['user_id', 'exp']
            for claim in required_claims:
                if claim not in payload:
                    return {
                        'valid': False,
                        'error_code': 'MISSING_CLAIM',
                        'error_message': f'Missing required claim: {claim}'
                    }
            
            return {
                'valid': True,
                'user_id': payload.get('user_id'),
                'email': payload.get('email'),
                'payload': payload,
                'error_code': None,
                'error_message': None
            }
            
        except jwt.ExpiredSignatureError:
            return {
                'valid': False,
                'error_code': 'TOKEN_EXPIRED',
                'error_message': 'Token has expired'
            }
            
        except jwt.InvalidSignatureError:
            return {
                'valid': False,
                'error_code': 'INVALID_SIGNATURE',
                'error_message': 'Token signature is invalid'
            }
            
        except jwt.DecodeError:
            return {
                'valid': False,
                'error_code': 'DECODE_ERROR',
                'error_message': 'Token could not be decoded'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in manual token validation: {str(e)}")
            return {
                'valid': False,
                'error_code': 'VALIDATION_ERROR',
                'error_message': 'Token validation failed'
            }


class RequestEnrichmentMiddleware(MiddlewareMixin):
    """
    Middleware para enriquecer requests con información adicional
    """
    
    def process_request(self, request):
        """
        Agregar información adicional al request
        """
        # Timestamp del request
        request.gateway_timestamp = int(time.time() * 1000)
        
        # ID único del request (para tracing)
        import uuid
        request.gateway_request_id = str(uuid.uuid4())
        
        # Información del cliente
        request.client_ip = self._get_client_ip(request)
        request.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return None
    
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
    
    def process_response(self, request, response):
        """
        Agregar headers adicionales a la response
        """
        # Agregar headers informativos
        response['X-Gateway-Service'] = 'pontificia-gateway'
        response['X-Gateway-Version'] = '1.0.0'
        
        if hasattr(request, 'gateway_request_id'):
            response['X-Request-ID'] = request.gateway_request_id
        
        if hasattr(request, 'gateway_timestamp'):
            import time
            response_time = int(time.time() * 1000) - request.gateway_timestamp
            response['X-Response-Time'] = f"{response_time}ms"
        
        return response