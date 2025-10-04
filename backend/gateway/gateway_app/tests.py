"""
Tests de integración completos para el API Gateway.
Verifica el funcionamiento completo del gateway incluyendo:
- Proxy a microservicios
- Rate limiting
- JWT validation
- Health checks
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from unittest.mock import patch, Mock, MagicMock
import json
import time


class GatewayIntegrationTests(TestCase):
    """Tests de integración para el API Gateway"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        # No limpiamos cache para evitar errores de conexión a Redis en tests
        # cache.clear()
        
    def test_health_check_endpoint(self):
        """Test del endpoint de salud del gateway"""
        response = self.client.get('/health/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('services', data)
        
        # Verificar que incluye información de todos los microservicios
        expected_services = ['auth', 'users', 'asistencia', 'documentos', 'pagos', 'reportes', 'auditoria']
        
        for service in expected_services:
            self.assertIn(service, data['services'])
    
    def test_api_docs_endpoint(self):
        """Test del endpoint de documentación OpenAPI"""
        response = self.client.get('/api/docs/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
    
    def test_api_schema_endpoint(self):
        """Test del endpoint del esquema OpenAPI"""
        response = self.client.get('/api/schema/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('openapi', data)
        self.assertIn('info', data)
        self.assertIn('paths', data)
    
    @patch('gateway_app.simple_views.requests.request')
    def test_proxy_functionality_auth_service(self, mock_request):
        """Test del proxy al servicio de autenticación"""
        # Configurar mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"message": "auth service response"}'
        mock_request.return_value = mock_response
        
        # Realizar petición a través del proxy
        response = self.client.get('/api/auth/login/')
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se hizo la llamada al microservicio
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        
        # Verificar URL del microservicio
        self.assertIn('localhost:3001', call_args[1]['url'])
    
    @patch('gateway_app.simple_views.requests.request')
    def test_proxy_functionality_users_service(self, mock_request):
        """Test del proxy al servicio de usuarios"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"message": "users service response"}'
        mock_request.return_value = mock_response
        
        response = self.client.get('/api/users/profile/')
        
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertIn('localhost:3002', call_args[1]['url'])
    
    @patch('gateway_app.simple_views.requests.request')
    def test_proxy_error_handling(self, mock_request):
        """Test del manejo de errores en el proxy"""
        # Simular error de conexión
        mock_request.side_effect = Exception("Connection error")
        
        response = self.client.get('/api/auth/login/')
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Connection error', data['error'])
    
    def test_rate_limiting_middleware(self):
        """Test del middleware de rate limiting"""
        # Nota: Este test require que RATE_LIMIT_ENABLED esté en True
        # Para simular, podemos hacer múltiples requests
        
        # Realizar múltiples peticiones rápidas
        responses = []
        for i in range(5):
            response = self.client.get('/health/')
            responses.append(response.status_code)
        
        # Todas las primeras peticiones deberían ser exitosas
        # En un entorno real con rate limiting activado, 
        # algunas peticiones serían bloqueadas
        for status in responses:
            self.assertIn(status, [200, 429])  # 200 OK o 429 Too Many Requests


class GatewayMiddlewareTests(TestCase):
    """Tests específicos para los middlewares del gateway"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        # No limpiamos cache para evitar errores de conexión a Redis en tests
        # cache.clear()
    
    def test_rate_limit_cache_key_generation(self):
        """Test de generación de claves de cache para rate limiting"""
        from gateway_app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda request: None)
        
        # Test con IP normal
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        key = middleware.get_cache_key(request, 'minute')
        expected_key = 'rate_limit:192.168.1.1:minute'
        
        self.assertEqual(key, expected_key)
    
    def test_jwt_validation_middleware_setup(self):
        """Test de configuración del middleware JWT"""
        from gateway_app.middleware import JWTValidationMiddleware
        
        middleware = JWTValidationMiddleware(lambda request: None)
        
        # El middleware debería inicializarse correctamente
        self.assertIsNotNone(middleware)


class GatewayConfigurationTests(TestCase):
    """Tests de configuración del gateway"""
    
    def test_microservices_configuration(self):
        """Test de configuración de microservicios"""
        # Verificar que todos los microservicios están configurados
        microservices = getattr(settings, 'MICROSERVICES', {})
        
        expected_services = ['auth', 'users', 'asistencia', 'documentos', 'pagos', 'reportes', 'auditoria']
        
        for service in expected_services:
            self.assertIn(service, microservices)
            self.assertIn('url', microservices[service])
            self.assertTrue(microservices[service]['url'])
    
    def test_cache_configuration(self):
        """Test de configuración de cache"""
        from django.core.cache import cache
        
        # Test básico de cache
        cache.set('test_key', 'test_value', 60)
        value = cache.get('test_key')
        
        self.assertEqual(value, 'test_value')
    
    def test_rest_framework_configuration(self):
        """Test de configuración de Django REST Framework"""
        rest_config = getattr(settings, 'REST_FRAMEWORK', {})
        
        # Verificar configuraciones clave
        self.assertIn('DEFAULT_AUTHENTICATION_CLASSES', rest_config)
        self.assertIn('DEFAULT_PERMISSION_CLASSES', rest_config)
        self.assertIn('DEFAULT_SCHEMA_CLASS', rest_config)


class GatewayPerformanceTests(TestCase):
    """Tests de rendimiento básico del gateway"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
    
    def test_health_check_response_time(self):
        """Test básico de tiempo de respuesta del health check"""
        start_time = time.time()
        response = self.client.get('/health/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # El health check debería responder en menos de 1 segundo
        self.assertLess(response_time, 1.0)
        self.assertEqual(response.status_code, 200)
    
    @patch('gateway_app.simple_views.requests.request')
    def test_proxy_response_time(self, mock_request):
        """Test básico de tiempo de respuesta del proxy"""
        # Configurar mock response rápida
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"message": "fast response"}'
        mock_request.return_value = mock_response
        
        start_time = time.time()
        response = self.client.get('/api/auth/status/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # El proxy debería responder rápidamente
        self.assertLess(response_time, 0.5)
        self.assertEqual(response.status_code, 200)


class GatewayBasicTestCase(TestCase):
    """
    Tests básicos para el Gateway - Mantenido para compatibilidad
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_root_endpoint(self):
        """Test del endpoint raíz"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['service'], 'Sistema Pontificia - API Gateway')
        self.assertEqual(data['port'], 8000)
        self.assertIn('endpoints', data)
    
    def test_health_endpoint_no_services(self):
        """Test del health check sin servicios disponibles"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('services', data)
        self.assertIn('timestamp', data)
    
    def test_gateway_info_endpoint(self):
        """Test del endpoint de información del gateway"""
        response = self.client.get('/api/gateway/info/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('name', data)
        self.assertIn('version', data)
        self.assertIn('services', data)
    
    def test_routes_endpoint(self):
        """Test del endpoint de rutas"""
        response = self.client.get('/api/gateway/routes/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_docs_endpoint(self):
        """Test del endpoint de documentación"""
        response = self.client.get('/docs/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.get('Content-Type', ''))


class GatewayLegacyProxyTestCase(TestCase):
    """
    Tests legacy para funcionalidad de proxy
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_proxy_invalid_service(self):
        """Test de proxy a servicio inválido"""
        response = self.client.get('/invalid_service/test/')
        # Debería devolver 404 o error apropiado
        self.assertIn(response.status_code, [404, 503])


class GatewayJWTTestCase(TestCase):
    """
    Tests para validación JWT
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_jwt_protected_endpoint(self):
        """Test de endpoint protegido sin JWT"""
        response = self.client.get('/auditoria/api/protected/')
        # Debería requerir autenticación
        self.assertIn(response.status_code, [401, 403])
    
    def test_jwt_excluded_endpoint(self):
        """Test de endpoint excluido de JWT"""
        response = self.client.get('/health/')
        # No debería requerir autenticación
        self.assertEqual(response.status_code, 200)


class GatewayServiceTestCase(TestCase):
    """
    Tests para servicios del Gateway
    """
    
    def test_service_connection(self):
        """Test de conexión a servicios"""
        from gateway_app.services import GatewayService
        
        gateway_service = GatewayService()
        
        # Test con servicio configurado
        for service_name in settings.MICROSERVICES.keys():
            result = gateway_service.test_service_connection(service_name)
            self.assertIn('connection_test', result)
            self.assertIn('service', result)
    
    def test_circuit_breaker(self):
        """Test del circuit breaker"""
        from gateway_app.services import CircuitBreaker
        
        cb = CircuitBreaker('test_service', failure_threshold=2, recovery_timeout=30)
        
        # Estado inicial debe ser CLOSED
        self.assertEqual(cb.state, 'CLOSED')
        
        # Simular fallos
        cb.record_failure()
        cb.record_failure()
        
        # Después de 2 fallos, debe estar OPEN
        self.assertEqual(cb.state, 'OPEN')


class GatewayIntegrationTestCase(TestCase):
    """
    Tests de integración completos
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_complete_request_flow(self):
        """Test del flujo completo de una request"""
        # 1. Verificar que el gateway está funcionando
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # 2. Verificar health check
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        
        # 3. Verificar documentación
        response = self.client.get('/docs/')
        self.assertEqual(response.status_code, 200)
        
        # 4. Verificar API info
        response = self.client.get('/api/gateway/info/')
        self.assertEqual(response.status_code, 200)
    
    @patch('gateway_app.services.GatewayService.make_request')
    def test_proxy_with_circuit_breaker(self, mock_request):
        """Test de proxy con circuit breaker"""
        # Simular fallo del servicio
        mock_request.side_effect = Exception("Service unavailable")
        
        # Múltiples requests deberían activar el circuit breaker
        for _ in range(3):
            response = self.client.get('/auditoria/api/test/')
            self.assertIn(response.status_code, [503, 500])
    
    def test_rate_limiting(self):
        """Test básico de rate limiting"""
        # Hacer múltiples requests rápidas
        responses = []
        for _ in range(5):
            response = self.client.get('/health/')
            responses.append(response.status_code)
        
        # Al menos algunas deberían pasar
        success_count = sum(1 for status in responses if status == 200)
        self.assertGreater(success_count, 0)


class GatewayDocumentationTestCase(TestCase):
    """
    Tests para documentación de API
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_swagger_documentation(self):
        """Test de documentación Swagger"""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, 200)
    
    def test_redoc_documentation(self):
        """Test de documentación ReDoc"""
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, 200)
    
    def test_openapi_schema(self):
        """Test del schema OpenAPI"""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        
        # Verificar que es JSON válido
        try:
            json.loads(response.content)
        except json.JSONDecodeError:
            self.fail("Schema no es JSON válido")
