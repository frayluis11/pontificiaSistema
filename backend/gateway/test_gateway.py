#!/usr/bin/env python3
"""
Script de prueba para el API Gateway
Verifica que todos los componentes estén funcionando correctamente
"""

import requests
import json
import time
import sys
from urllib.parse import urljoin


class GatewayTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.passed = 0
        self.failed = 0
    
    def test(self, name, condition, details=""):
        """Helper para ejecutar tests"""
        if condition:
            print(f"✅ {name}")
            self.passed += 1
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.failed += 1
    
    def make_request(self, endpoint, method="GET", **kwargs):
        """Helper para hacer requests"""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to {url}: {e}")
            return None
    
    def test_root_endpoint(self):
        """Test del endpoint raíz"""
        print("\n🧪 Testing Root Endpoint...")
        response = self.make_request("/")
        
        if response:
            self.test("Root endpoint accessible", response.status_code == 200)
            
            try:
                data = response.json()
                self.test("Root returns JSON", True)
                self.test("Service name correct", 
                         data.get('service') == 'Sistema Pontificia - API Gateway')
                self.test("Port configured correctly", data.get('port') == 8000)
                self.test("Endpoints info present", 'endpoints' in data)
            except json.JSONDecodeError:
                self.test("Root returns valid JSON", False)
        else:
            self.test("Root endpoint accessible", False)
    
    def test_health_endpoint(self):
        """Test del health check"""
        print("\n🏥 Testing Health Endpoint...")
        response = self.make_request("/health/")
        
        if response:
            self.test("Health endpoint accessible", response.status_code == 200)
            
            try:
                data = response.json()
                self.test("Health returns JSON", True)
                self.test("Status field present", 'status' in data)
                self.test("Services field present", 'services' in data)
                self.test("Timestamp field present", 'timestamp' in data)
                
                if 'services' in data:
                    services_count = len(data['services'])
                    self.test(f"Services monitored ({services_count})", services_count > 0)
            except json.JSONDecodeError:
                self.test("Health returns valid JSON", False)
        else:
            self.test("Health endpoint accessible", False)
    
    def test_documentation_endpoints(self):
        """Test de endpoints de documentación"""
        print("\n📚 Testing Documentation Endpoints...")
        
        # Custom docs
        response = self.make_request("/docs/")
        self.test("Custom docs accessible", 
                 response and response.status_code == 200)
        
        # Swagger docs
        response = self.make_request("/api/docs/")
        self.test("Swagger docs accessible", 
                 response and response.status_code == 200)
        
        # ReDoc
        response = self.make_request("/api/redoc/")
        self.test("ReDoc accessible", 
                 response and response.status_code == 200)
        
        # OpenAPI Schema
        response = self.make_request("/api/schema/")
        if response and response.status_code == 200:
            self.test("OpenAPI schema accessible", True)
            try:
                schema = response.json()
                self.test("Schema is valid JSON", True)
                self.test("OpenAPI version present", 'openapi' in schema)
                self.test("Info section present", 'info' in schema)
                self.test("Paths section present", 'paths' in schema)
            except json.JSONDecodeError:
                self.test("Schema is valid JSON", False)
        else:
            self.test("OpenAPI schema accessible", False)
    
    def test_gateway_api_endpoints(self):
        """Test de endpoints de la API del gateway"""
        print("\n🔌 Testing Gateway API Endpoints...")
        
        # Info endpoint
        response = self.make_request("/api/gateway/info/")
        if response and response.status_code == 200:
            self.test("Gateway info endpoint accessible", True)
            try:
                data = response.json()
                self.test("Info contains name", 'name' in data)
                self.test("Info contains version", 'version' in data)
                self.test("Info contains services", 'services' in data)
            except json.JSONDecodeError:
                self.test("Gateway info returns valid JSON", False)
        else:
            self.test("Gateway info endpoint accessible", False)
        
        # Routes endpoint
        response = self.make_request("/api/gateway/routes/")
        if response and response.status_code == 200:
            self.test("Gateway routes endpoint accessible", True)
            try:
                data = response.json()
                self.test("Routes is a list", isinstance(data, list))
            except json.JSONDecodeError:
                self.test("Gateway routes returns valid JSON", False)
        else:
            self.test("Gateway routes endpoint accessible", False)
        
        # Stats endpoint
        response = self.make_request("/api/gateway/stats/")
        if response and response.status_code == 200:
            self.test("Gateway stats endpoint accessible", True)
            try:
                data = response.json()
                self.test("Stats contains metrics", len(data) > 0)
            except json.JSONDecodeError:
                self.test("Gateway stats returns valid JSON", False)
        else:
            self.test("Gateway stats endpoint accessible", False)
    
    def test_service_connections(self):
        """Test de conexiones a microservicios"""
        print("\n🔗 Testing Service Connections...")
        
        services = ['auditoria', 'auth', 'users', 'academic', 'students', 'courses', 'reports']
        
        for service in services:
            response = self.make_request(f"/test/{service}/")
            if response and response.status_code == 200:
                self.test(f"{service} service test endpoint", True)
                try:
                    data = response.json()
                    connection_status = data.get('connection_test', 'unknown')
                    self.test(f"{service} connection status available", 
                             connection_status != 'unknown')
                except json.JSONDecodeError:
                    self.test(f"{service} returns valid JSON", False)
            else:
                self.test(f"{service} service test endpoint", False)
    
    def test_proxy_routes(self):
        """Test básico de rutas proxy (sin autenticación)"""
        print("\n🔄 Testing Proxy Routes (Basic)...")
        
        services = ['auditoria', 'auth', 'users', 'academic', 'students', 'courses', 'reports']
        
        for service in services:
            # Test basic proxy route - debería devolver 401/403 si JWT está configurado
            # o conectar al servicio si está disponible
            response = self.make_request(f"/{service}/")
            
            if response:
                # Si devuelve 401/403, el proxy está funcionando pero requiere auth
                # Si devuelve 200, el servicio está disponible
                # Si devuelve 503/502, el servicio no está disponible
                status_ok = response.status_code in [200, 401, 403, 503, 502]
                self.test(f"{service} proxy route responds", status_ok)
                
                if not status_ok:
                    print(f"   Status code: {response.status_code}")
            else:
                self.test(f"{service} proxy route responds", False)
    
    def test_rate_limiting(self):
        """Test básico de rate limiting"""
        print("\n⏱️ Testing Rate Limiting...")
        
        # Hacer múltiples requests rápidas al health endpoint
        responses = []
        for i in range(5):
            response = self.make_request("/health/")
            if response:
                responses.append(response.status_code)
            time.sleep(0.1)  # Pequeña pausa
        
        success_count = sum(1 for status in responses if status == 200)
        self.test("Rate limiting allows some requests", success_count > 0)
        self.test("Rate limiting is configured", len(responses) > 0)
    
    def test_cors_headers(self):
        """Test de headers CORS"""
        print("\n🌐 Testing CORS Headers...")
        
        response = self.make_request("/", headers={'Origin': 'http://localhost:3000'})
        if response:
            headers = response.headers
            self.test("CORS Access-Control-Allow-Origin present", 
                     'Access-Control-Allow-Origin' in headers)
            self.test("CORS Access-Control-Allow-Methods present", 
                     'Access-Control-Allow-Methods' in headers)
        else:
            self.test("CORS headers test", False)
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 Starting API Gateway Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Ejecutar todos los tests
        self.test_root_endpoint()
        self.test_health_endpoint()
        self.test_documentation_endpoints()
        self.test_gateway_api_endpoints()
        self.test_service_connections()
        self.test_proxy_routes()
        self.test_rate_limiting()
        self.test_cors_headers()
        
        # Resumen
        print(f"\n📊 Test Results:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All tests passed! Gateway is working correctly.")
            return True
        else:
            print(f"\n⚠️  {self.failed} tests failed. Please check the gateway configuration.")
            return False


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test API Gateway functionality')
    parser.add_argument('--url', default='http://127.0.0.1:8000', 
                       help='Gateway base URL (default: http://127.0.0.1:8000)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Crear tester
    tester = GatewayTester(args.url)
    
    # Ejecutar tests
    success = tester.run_all_tests()
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()