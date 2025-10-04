"""
Services para el API Gateway
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
import time
import json
from urllib.parse import urljoin

logger = logging.getLogger('gateway')


class MicroserviceClient:
    """
    Cliente para comunicación con microservicios
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.config = settings.MICROSERVICES.get(service_name, {})
        self.base_url = self.config.get('url', '')
        self.timeout = self.config.get('timeout', 30)
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.health_endpoint = self.config.get('health_endpoint', '/api/health/')
    
    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Hacer request a microservicio con retry y error handling
        """
        url = urljoin(self.base_url, path)
        kwargs.setdefault('timeout', self.timeout)
        
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Attempt {attempt + 1} - {method} {url}")
                
                response = requests.request(method, url, **kwargs)
                
                # Log successful request
                logger.info(f"Success - {method} {url} -> {response.status_code}")
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed - {method} {url}: {str(e)}")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # All attempts failed
        logger.error(f"All attempts failed - {method} {url}: {str(last_exception)}")
        raise last_exception
    
    def get(self, path: str, **kwargs) -> requests.Response:
        """GET request al microservicio"""
        return self._make_request('GET', path, **kwargs)
    
    def post(self, path: str, **kwargs) -> requests.Response:
        """POST request al microservicio"""
        return self._make_request('POST', path, **kwargs)
    
    def put(self, path: str, **kwargs) -> requests.Response:
        """PUT request al microservicio"""
        return self._make_request('PUT', path, **kwargs)
    
    def patch(self, path: str, **kwargs) -> requests.Response:
        """PATCH request al microservicio"""
        return self._make_request('PATCH', path, **kwargs)
    
    def delete(self, path: str, **kwargs) -> requests.Response:
        """DELETE request al microservicio"""
        return self._make_request('DELETE', path, **kwargs)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar salud del microservicio
        """
        cache_key = f"health_{self.service_name}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            response = self.get(self.health_endpoint)
            
            if response.status_code == 200:
                result = {
                    'service': self.service_name,
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'details': response.json() if response.content else {}
                }
            else:
                result = {
                    'service': self.service_name,
                    'status': 'unhealthy',
                    'response_time': response.elapsed.total_seconds(),
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            result = {
                'service': self.service_name,
                'status': 'unhealthy',
                'response_time': None,
                'error': str(e)
            }
        
        # Cache result for 30 seconds
        cache.set(cache_key, result, 30)
        return result


class GatewayService:
    """
    Servicio principal del Gateway
    """
    
    def __init__(self):
        self.clients = {
            name: MicroserviceClient(name) 
            for name in settings.MICROSERVICES.keys()
        }
    
    def get_client(self, service_name: str) -> Optional[MicroserviceClient]:
        """
        Obtener cliente para un microservicio específico
        """
        return self.clients.get(service_name)
    
    def proxy_request(self, service_name: str, method: str, path: str, 
                     headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Proxear request a microservicio específico
        """
        client = self.get_client(service_name)
        if not client:
            raise ValueError(f"Unknown service: {service_name}")
        
        # Preparar headers
        if headers:
            # Filtrar headers internos de Django
            filtered_headers = {
                k: v for k, v in headers.items() 
                if not k.startswith('HTTP_') and k.lower() not in ['host', 'content-length']
            }
            kwargs['headers'] = filtered_headers
        
        # Hacer request
        return client._make_request(method, path, **kwargs)
    
    def health_check_all(self) -> Dict[str, Any]:
        """
        Verificar salud de todos los microservicios
        """
        results = {}
        overall_healthy = True
        
        for service_name, client in self.clients.items():
            try:
                health = client.health_check()
                results[service_name] = health
                
                if health['status'] != 'healthy':
                    overall_healthy = False
                    
            except Exception as e:
                results[service_name] = {
                    'service': service_name,
                    'status': 'error',
                    'error': str(e)
                }
                overall_healthy = False
        
        return {
            'gateway': {
                'status': 'healthy' if overall_healthy else 'degraded',
                'timestamp': time.time(),
                'services': results
            }
        }
    
    def get_service_routes(self) -> Dict[str, List[str]]:
        """
        Obtener rutas disponibles para cada servicio
        """
        routes = {}
        
        for service_name in self.clients.keys():
            routes[service_name] = [
                f"/api/{service_name}/",
                f"/api/{service_name}/*"
            ]
        
        return routes


class CircuitBreaker:
    """
    Circuit breaker para microservicios
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.failure_threshold = settings.CIRCUIT_BREAKER['failure_threshold']
        self.recovery_timeout = settings.CIRCUIT_BREAKER['recovery_timeout']
        self.reset()
    
    def reset(self):
        """Resetear circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self):
        """Registrar éxito"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def record_failure(self):
        """Registrar fallo"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
    
    def can_request(self) -> bool:
        """Verificar si se puede hacer request"""
        if self.state == 'CLOSED':
            return True
        
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def is_open(self) -> bool:
        """Verificar si el circuit breaker está abierto"""
        return self.state == 'OPEN'


class LoadBalancer:
    """
    Load balancer simple para múltiples instancias
    """
    
    def __init__(self, instances: List[str]):
        self.instances = instances
        self.current_index = 0
    
    def get_next_instance(self) -> str:
        """
        Obtener siguiente instancia (round-robin)
        """
        if not self.instances:
            raise ValueError("No instances available")
        
        instance = self.instances[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.instances)
        return instance


class RequestLogger:
    """
    Logger especializado para requests del gateway
    """
    
    @staticmethod
    def log_request(service_name: str, method: str, path: str, 
                   response_code: int, response_time: float, 
                   user_id: Optional[int] = None):
        """
        Registrar request en logs
        """
        logger.info(
            f"PROXY {service_name} - {method} {path} -> {response_code} "
            f"({response_time:.3f}s) [user: {user_id or 'anonymous'}]"
        )
    
    @staticmethod
    def log_error(service_name: str, method: str, path: str, error: str):
        """
        Registrar error en logs
        """
        logger.error(f"PROXY ERROR {service_name} - {method} {path}: {error}")


# Instancias globales
gateway_service = GatewayService()
circuit_breakers = {
    name: CircuitBreaker(name) 
    for name in settings.MICROSERVICES.keys()
}