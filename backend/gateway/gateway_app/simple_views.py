"""
Views simplificadas para el API Gateway
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from datetime import datetime
import time


@api_view(['GET'])
@permission_classes([AllowAny])
def root_view(request):
    """
    Vista principal del Gateway
    """
    return JsonResponse({
        'service': 'Sistema Pontificia - API Gateway',
        'version': '1.0.0',
        'status': 'online',
        'port': 8000,
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': '/health/',
            'docs': '/docs/',
            'api_docs': '/api/docs/',
            'gateway_info': '/api/gateway/',
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check completo que verifica todos los microservicios
    """
    import requests
    from django.conf import settings
    
    # Configuración de los microservicios
    microservices = {
        'auth': 'http://localhost:3001/api/health/',
        'users': 'http://localhost:3002/api/health/',
        'asistencia': 'http://localhost:3003/api/health/',
        'documentos': 'http://localhost:3004/api/health/',
        'pagos': 'http://localhost:3005/api/health/',
        'reportes': 'http://localhost:3006/api/health/',
        'auditoria': 'http://localhost:3007/api/health/',
    }
    
    services_status = {}
    healthy_services = 0
    unhealthy_services = 0
    
    # Verificar cada microservicio
    for service_name, health_url in microservices.items():
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                services_status[service_name] = {
                    'status': 'healthy',
                    'response_time_ms': response.elapsed.total_seconds() * 1000,
                    'url': health_url
                }
                healthy_services += 1
            else:
                services_status[service_name] = {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'url': health_url
                }
                unhealthy_services += 1
        except requests.exceptions.RequestException as e:
            services_status[service_name] = {
                'status': 'unreachable',
                'error': str(e),
                'url': health_url
            }
            unhealthy_services += 1
    
    # Determinar estado general
    overall_status = 'healthy' if unhealthy_services == 0 else 'degraded' if healthy_services > 0 else 'unhealthy'
    
    return JsonResponse({
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'gateway': {
            'status': 'running',
            'version': '1.0.0',
            'port': 8000
        },
        'services': services_status,
        'summary': {
            'total_services': len(microservices),
            'healthy_services': healthy_services,
            'unhealthy_services': unhealthy_services,
            'overall_health_percentage': round((healthy_services / len(microservices)) * 100, 1)
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def gateway_info(request):
    """
    Información del gateway
    """
    return JsonResponse({
        'name': 'Sistema Pontificia API Gateway',
        'version': '1.0.0',
        'status': 'running',
        'port': 8000,
        'timestamp': datetime.now().isoformat(),
        'services': ['auth', 'users', 'academic', 'students', 'courses', 'reports', 'auditoria'],
        'features': {
            'proxy': True,
            'jwt_validation': False,  # Temporalmente deshabilitado
            'rate_limiting': False,   # Temporalmente deshabilitado
            'health_monitoring': True,
            'circuit_breaker': True
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def docs_view(request):
    """
    Documentación personalizada
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Gateway - Sistema Pontificia</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #333; border-bottom: 2px solid #007cba; padding-bottom: 20px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { background: #007cba; color: white; padding: 5px 10px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Sistema Pontificia - API Gateway</h1>
            <p>Puerto: 8000 | Version: 1.0.0 | Estado: Online</p>
        </div>
        
        <h2>📚 Endpoints Disponibles</h2>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/</strong><br>
            Información principal del gateway
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/health/</strong><br>
            Health check de todos los microservicios
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/api/gateway/</strong><br>
            Información detallada del gateway
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/api/docs/</strong><br>
            Documentación Swagger/OpenAPI
        </div>
        
        <h2>🔗 Microservicios</h2>
        <ul>
            <li><strong>Auth:</strong> /auth/* → localhost:3001</li>
            <li><strong>Users:</strong> /users/* → localhost:3002</li>
            <li><strong>Academic:</strong> /academic/* → localhost:3004</li>
            <li><strong>Students:</strong> /students/* → localhost:3005</li>
            <li><strong>Courses:</strong> /courses/* → localhost:3006</li>
            <li><strong>Reports:</strong> /reports/* → localhost:3007</li>
            <li><strong>Auditoria:</strong> /auditoria/* → localhost:8001</li>
        </ul>
        
        <footer style="margin-top: 40px; color: #666;">
            <p>Sistema Pontificia &copy; 2025</p>
        </footer>
    </body>
    </html>
    """
    
    from django.http import HttpResponse
    return HttpResponse(html_content, content_type='text/html')


# ========== PROXY FUNCTIONS ==========

import requests
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

def create_proxy_view(service_name, base_url):
    """
    Factory function para crear vistas de proxy
    """
    @api_view(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    @permission_classes([AllowAny])  # Temporalmente permitir todo
    def proxy_view(request, path=''):
        try:
            # Construir URL completa
            target_url = f"{base_url}/api/{path}"
            
            # Preparar headers
            headers = {}
            for key, value in request.META.items():
                if key.startswith('HTTP_'):
                    header_name = key[5:].replace('_', '-').title()
                    if header_name not in ['Host', 'Content-Length']:
                        headers[header_name] = value
            
            # Añadir Content-Type si es necesario
            if hasattr(request, 'content_type') and request.content_type:
                headers['Content-Type'] = request.content_type
            
            # Preparar datos según el método
            data = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.body
            
            # Preparar parámetros de query
            params = request.GET.dict()
            
            # Hacer la request
            response = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=data,
                params=params,
                timeout=30,
                allow_redirects=False
            )
            
            # Crear respuesta
            if response.headers.get('content-type', '').startswith('application/json'):
                return JsonResponse(
                    response.json() if response.content else {},
                    status=response.status_code
                )
            else:
                return HttpResponse(
                    response.content,
                    status=response.status_code,
                    content_type=response.headers.get('content-type', 'text/plain')
                )
            
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'error': f'Error connecting to {service_name} service',
                'detail': str(e),
                'service': service_name,
                'target_url': target_url
            }, status=503)
        except Exception as e:
            return JsonResponse({
                'error': f'Proxy error for {service_name}',
                'detail': str(e),
                'service': service_name
            }, status=500)
    
    return proxy_view

# Crear vistas de proxy para cada microservicio
proxy_auth = create_proxy_view('auth', 'http://localhost:3001')
proxy_users = create_proxy_view('users', 'http://localhost:3002')
proxy_asistencia = create_proxy_view('asistencia', 'http://localhost:3003')
proxy_documentos = create_proxy_view('documentos', 'http://localhost:3004')
proxy_pagos = create_proxy_view('pagos', 'http://localhost:3005')
proxy_reportes = create_proxy_view('reportes', 'http://localhost:3006')
proxy_auditoria = create_proxy_view('auditoria', 'http://localhost:3007')