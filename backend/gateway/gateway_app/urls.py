"""
URL Configuration para el API Gateway
"""

from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'gateway', views.GatewayViewSet, basename='gateway')

app_name = 'gateway_app'

urlpatterns = [
    # API Router
    path('api/', include(router.urls)),
    
    # Health check endpoint
    path('health/', views.health_check, name='health_check'),
    
    # Documentation
    path('docs/', views.DocumentationView.as_view(), name='docs'),
    
    # Service connection test
    path('test/<str:service_name>/', views.test_service_connection, name='test_service'),
    
    # Proxy routes para microservicios
    # IMPORTANTE: Estas rutas deben ir al final para no interceptar otras rutas
    
    # Auditoria Service
    re_path(r'^auditoria/(?P<path>.*)$', views.ProxyView.as_view(), 
            {'service_name': 'auditoria'}, name='proxy_auditoria'),
    
    # Auth Service
    re_path(r'^auth/(?P<path>.*)$', views.ProxyView.as_view(), 
            {'service_name': 'auth'}, name='proxy_auth'),
    
    # User Management Service
    re_path(r'^users/(?P<path>.*)$', views.ProxyView.as_view(), 
            {'service_name': 'users'}, name='proxy_users'),
    
    # Academic Service
    re_path(r'^academic/(?P<path>.*)$', views.ProxyView.as_view(), 
            {'service_name': 'academic'}, name='proxy_academic'),
    
    # Student Service
    re_path(r'^students/(?P<path>.*)$', views.ProxyView.as_view(), 
            {'service_name': 'students'}, name='proxy_students'),
    
    # Courses Service
    re_path(r'^courses/(?P<path>.*)$', views.ProxyView.as_view(), 
            {'service_name': 'courses'}, name='proxy_courses'),
    
    # Reports Service
    re_path(r'^reports/(?P<path>.*)$', views.ProxyView.as_view(), 
            {'service_name': 'reports'}, name='proxy_reports'),
]

# Información de rutas para documentación
GATEWAY_ROUTES_INFO = {
    'api_endpoints': {
        '/api/gateway/': 'Información del gateway',
        '/api/gateway/info/': 'Información detallada del gateway',
        '/api/gateway/routes/': 'Lista de rutas disponibles',
        '/api/gateway/stats/': 'Estadísticas del gateway',
        '/health/': 'Health check de todos los servicios',
        '/docs/': 'Documentación de la API',
        '/test/<service>/': 'Test de conexión a servicio específico',
    },
    'proxy_routes': {
        '/auditoria/*': 'Proxy al servicio de auditoría (puerto 8001)',
        '/auth/*': 'Proxy al servicio de autenticación (puerto 8002)',
        '/users/*': 'Proxy al servicio de usuarios (puerto 8003)',
        '/academic/*': 'Proxy al servicio académico (puerto 8004)',
        '/students/*': 'Proxy al servicio de estudiantes (puerto 8005)',
        '/courses/*': 'Proxy al servicio de cursos (puerto 8006)',
        '/reports/*': 'Proxy al servicio de reportes (puerto 8007)',
    },
    'authentication': {
        'excluded_paths': ['/health/', '/docs/', '/api/gateway/info/', '/test/'],
        'jwt_required': 'Todas las rutas proxy requieren JWT válido',
        'header_format': 'Authorization: Bearer <token>',
    },
    'rate_limiting': {
        'health_check': '30 requests per minute',
        'api_endpoints': '60 requests per minute',
        'proxy_routes': '100 requests per minute',
    }
}