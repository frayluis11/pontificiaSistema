"""
URLs híbridas para el API Gateway - Funcionales y Completas
"""

from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import simple_views
from . import views

# Router para ViewSets (si funcionan)
router = DefaultRouter()

try:
    # Intentar registrar el ViewSet complejo
    router.register(r'gateway', views.GatewayViewSet, basename='gateway')
    USE_COMPLEX_VIEWS = True
except Exception:
    # Si falla, usar views simples
    USE_COMPLEX_VIEWS = False

app_name = 'gateway_app'

if USE_COMPLEX_VIEWS:
    # Configuración completa con ViewSets
    urlpatterns = [
        # Endpoints básicos que siempre funcionan
        path('', simple_views.root_view, name='root'),
        path('health/', simple_views.health_check, name='health'),
        path('docs/', simple_views.docs_view, name='docs'),
        
        # API Router (complejo)
        path('api/', include(router.urls)),
        
        # Endpoints adicionales
        path('test/<str:service_name>/', views.test_service_connection, name='test_service'),
    ]
else:
    # Configuración simplificada que siempre funciona
    urlpatterns = [
        # Endpoints básicos
        path('', simple_views.root_view, name='root'),
        path('health/', simple_views.health_check, name='health'),
        path('docs/', simple_views.docs_view, name='docs'),
        path('api/gateway/', simple_views.gateway_info, name='gateway_info'),
    ]

# Información de rutas para documentación
GATEWAY_ROUTES_INFO = {
    'api_endpoints': {
        '/': 'Página principal del gateway',
        '/health/': 'Health check de todos los servicios',
        '/docs/': 'Documentación de la API',
        '/api/gateway/': 'Información del gateway',
    },
    'authentication': {
        'excluded_paths': ['/health/', '/docs/', '/api/gateway/', '/'],
        'description': 'Rutas públicas que no requieren autenticación',
    },
    'status': 'hybrid' if USE_COMPLEX_VIEWS else 'simplified'
}