"""
Views para el API Gateway
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import logging
from datetime import datetime

from .services import GatewayService
from .serializers import (
    GatewayInfoSerializer,
    RouteInfoSerializer,
    HealthCheckSerializer,
    GatewayStatsSerializer,
    ServiceConnectionTestSerializer,
    ErrorResponseSerializer,
    ServiceStatusSerializer
)
import time
import json

logger = logging.getLogger('gateway')

# Instancia global del servicio gateway
gateway_service = GatewayService()


class GatewayViewSet(viewsets.ViewSet):
    """
    ViewSet principal del Gateway con información y utilidades
    """
    
    @extend_schema(
        summary="Información del Gateway",
        description="Obtiene información general del API Gateway",
        responses={200: GatewayInfoSerializer}
    )
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def info(self, request):
        """
        Información del gateway
        GET /api/gateway/info/
        """
        info = {
            'name': 'Sistema Pontificia API Gateway',
            'version': '1.0.0',
            'status': 'running',
            'port': 8000,
            'timestamp': datetime.now().isoformat(),
            'services': list(gateway_service.clients.keys()),
            'features': {
                'proxy': True,
                'jwt_validation': True,
                'rate_limiting': True,
                'health_checks': True,
                'documentation': True,
                'circuit_breaker': True
            },
            'endpoints': {
                'health': '/health/',
                'docs': '/api/docs/',
                'schema': '/api/schema/',
                'gateway_info': '/api/gateway/info/',
                'routes': '/api/gateway/routes/'
            }
        }
        
        return Response(info)
    
    @extend_schema(
        summary="Rutas disponibles",
        description="Lista todas las rutas disponibles a través del gateway",
        responses={200: RouteInfoSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def routes(self, request):
        """
        Listar rutas disponibles
        GET /api/gateway/routes/
        """
        routes = []
        
        for service_name, client in gateway_service.clients.items():
            base_url = client.base_url
            routes.append({
                'service': service_name,
                'base_url': base_url,
                'gateway_routes': [
                    f"/api/{service_name}/",
                    f"/api/{service_name}/*"
                ],
                'health_endpoint': client.health_endpoint,
                'status': 'active'
            })
        
        return Response(routes)
    
    @extend_schema(
        summary="Estadísticas del Gateway",
        description="Obtiene estadísticas de uso del gateway",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        """
        Estadísticas del gateway
        GET /api/gateway/stats/
        """
        # En un sistema real, estas estadísticas vendrían de una base de datos o cache
        stats = {
            'total_requests': 0,  # Se implementaría con contadores reales
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'active_services': len([
                name for name, client in gateway_service.clients.items()
                if client.health_check().get('status') == 'healthy'
            ]),
            'total_services': len(gateway_service.clients),
            'uptime': '0 days, 0 hours, 0 minutes',  # Se calcularía desde el inicio
            'last_reset': datetime.now().isoformat()
        }
        
        return Response(stats)


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(
    summary="Health Check Completo",
    description="Verifica el estado de salud del gateway y todos los microservicios",
    responses={200: HealthCheckSerializer}
)
def health_check(request):
    """
    Health check completo del sistema
    GET /health/
    """
    try:
        # Verificar salud de todos los microservicios
        health_result = gateway_service.health_check_all()
        
        # Determinar status general
        gateway_info = health_result['gateway']
        overall_status = gateway_info['status']
        
        # Preparar respuesta
        response_data = {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'gateway': {
                'status': 'healthy',
                'version': '1.0.0',
                'uptime': '0 days',  # Se implementaría contador real
            },
            'services': gateway_info['services'],
            'summary': {
                'total_services': len(gateway_info['services']),
                'healthy_services': len([
                    s for s in gateway_info['services'].values() 
                    if s.get('status') == 'healthy'
                ]),
                'unhealthy_services': len([
                    s for s in gateway_info['services'].values() 
                    if s.get('status') != 'healthy'
                ])
            }
        }
        
        # Status code basado en la salud general
        status_code = 200 if overall_status == 'healthy' else 503
        
        return Response(response_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return Response(
            {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': 'Health check failed',
                'details': str(e)
            },
            status=500
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(
    summary="Health Check Simple",
    description="Health check simple del gateway",
    responses={200: OpenApiTypes.OBJECT}
)
def simple_health(request):
    """
    Health check simple
    GET /api/gateway/health/
    """
    return Response({
        'status': 'healthy',
        'service': 'gateway',
        'timestamp': datetime.now().isoformat()
    })


@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])  # La validación se hace en middleware
def proxy_view(request, service_name, path=''):
    """
    Vista proxy genérica para todos los microservicios
    Este endpoint maneja todas las rutas /api/{service}/...
    """
    # Esta vista en realidad no debería ejecutarse porque
    # el ProxyMiddleware intercepta las requests antes
    return JsonResponse(
        {
            'error': 'Proxy middleware not configured correctly',
            'service': service_name,
            'path': path
        },
        status=500
    )


class DocumentationView(View):
    """
    Vista personalizada para documentación
    """
    
    def get(self, request):
        """
        Página de documentación personalizada
        """
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema Pontificia API Gateway</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #007cba; color: white; padding: 20px; margin-bottom: 20px; }
                .section { margin: 20px 0; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 4px solid #007cba; }
                a { color: #007cba; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Sistema Pontificia API Gateway</h1>
                <p>Documentación de API centralizada</p>
            </div>
            
            <div class="section">
                <h2>Documentación Interactiva</h2>
                <p>Accede a la documentación OpenAPI interactiva:</p>
                <div class="endpoint">
                    <strong><a href="/api/docs/">🔗 Swagger UI - /api/docs/</a></strong><br>
                    Interfaz interactiva para explorar y probar la API
                </div>
                <div class="endpoint">
                    <strong><a href="/api/schema/">🔗 OpenAPI Schema - /api/schema/</a></strong><br>
                    Esquema OpenAPI en formato JSON
                </div>
            </div>
            
            <div class="section">
                <h2>Servicios Disponibles</h2>
                <div class="endpoint">
                    <strong>🔐 Auth Service</strong> - <code>/api/auth/</code><br>
                    Autenticación y autorización
                </div>
                <div class="endpoint">
                    <strong>👥 Users Service</strong> - <code>/api/users/</code><br>
                    Gestión de usuarios y perfiles
                </div>
                <div class="endpoint">
                    <strong>📋 Attendance Service</strong> - <code>/api/attendance/</code><br>
                    Control de asistencias
                </div>
                <div class="endpoint">
                    <strong>💰 Payments Service</strong> - <code>/api/payments/</code><br>
                    Gestión de pagos
                </div>
                <div class="endpoint">
                    <strong>📄 Documents Service</strong> - <code>/api/documents/</code><br>
                    Gestión de documentos
                </div>
                <div class="endpoint">
                    <strong>📊 Reports Service</strong> - <code>/api/reports/</code><br>
                    Generación de reportes
                </div>
                <div class="endpoint">
                    <strong>🔍 Audit Service</strong> - <code>/api/audit/</code><br>
                    Auditoría del sistema
                </div>
            </div>
            
            <div class="section">
                <h2>Gateway Endpoints</h2>
                <div class="endpoint">
                    <strong><a href="/health/">🩺 Health Check - /health/</a></strong><br>
                    Estado de salud de todos los servicios
                </div>
                <div class="endpoint">
                    <strong><a href="/api/gateway/info/">ℹ️ Gateway Info - /api/gateway/info/</a></strong><br>
                    Información del gateway
                </div>
                <div class="endpoint">
                    <strong><a href="/api/gateway/routes/">🛣️ Routes - /api/gateway/routes/</a></strong><br>
                    Lista de rutas disponibles
                </div>
            </div>
            
            <div class="section">
                <h2>Autenticación</h2>
                <p>Este gateway utiliza JWT (JSON Web Tokens) para autenticación:</p>
                <div class="endpoint">
                    <strong>Header:</strong> <code>Authorization: Bearer &lt;token&gt;</code><br>
                    <strong>Obtener token:</strong> <code>POST /api/auth/login/</code>
                </div>
            </div>
        </body>
        </html>
        """)


@api_view(['POST'])
@permission_classes([AllowAny])
@extend_schema(
    summary="Test de conexión a servicio",
    description="Prueba la conexión a un microservicio específico",
    parameters=[
        OpenApiParameter(
            name='service_name',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Nombre del servicio a probar'
        )
    ]
)
def test_service_connection(request, service_name):
    """
    Test de conexión a servicio específico
    POST /api/gateway/test/{service_name}/
    """
    client = gateway_service.get_client(service_name)
    if not client:
        return Response(
            {'error': f'Service {service_name} not found'},
            status=404
        )
    
    try:
        start_time = time.time()
        health = client.health_check()
        response_time = time.time() - start_time
        
        return Response({
            'service': service_name,
            'connection_test': 'success',
            'response_time': f"{response_time:.3f}s",
            'health_status': health.get('status'),
            'base_url': client.base_url,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'service': service_name,
            'connection_test': 'failed',
            'error': str(e),
            'base_url': client.base_url,
            'timestamp': datetime.now().isoformat()
        }, status=503)


class ProxyView(View):
    """
    Vista genérica para proxy de requests a microservicios
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Despacha requests a microservicios
        """
        service_name = kwargs.get('service_name')
        path = kwargs.get('path', '')
        
        if not service_name:
            return JsonResponse({'error': 'Service name required'}, status=400)
        
        client = gateway_service.get_client(service_name)
        if not client:
            return JsonResponse(
                {'error': f'Service {service_name} not found'}, 
                status=404
            )
        
        try:
            # Construir la URL completa
            url = f"{client.base_url}/{path}"
            
            # Preparar headers (excluir algunos headers internos)
            headers = {}
            for key, value in request.META.items():
                if key.startswith('HTTP_') and key not in ['HTTP_HOST']:
                    header_name = key[5:].replace('_', '-')
                    headers[header_name] = value
            
            # Preparar datos
            data = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.content_type == 'application/json':
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                    except:
                        data = request.body
                else:
                    data = request.POST.dict()
            
            # Hacer la request al microservicio
            response = client.make_request(
                method=request.method,
                path=path,
                headers=headers,
                data=data,
                params=request.GET.dict()
            )
            
            # Retornar la respuesta
            return JsonResponse(
                response.get('content', {}),
                status=response.get('status_code', 200),
                safe=False
            )
            
        except Exception as e:
            logger.error(f"Error proxying to {service_name}: {str(e)}")
            return JsonResponse(
                {
                    'error': 'Service unavailable',
                    'details': str(e),
                    'service': service_name
                },
                status=503
            )
