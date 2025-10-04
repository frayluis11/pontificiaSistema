"""
URLs para el servicio de documentos

Define las rutas de la API REST para documentos, versiones,
solicitudes y otras funcionalidades del sistema
"""
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentoViewSet,
    SolicitudDocumentoViewSet,
    EstadisticasView,
    OpcionesView
)

# Router para los ViewSets
router = DefaultRouter()
router.register(r'documentos', DocumentoViewSet, basename='documento')
router.register(r'solicitudes', SolicitudDocumentoViewSet, basename='solicitud')
router.register(r'estadisticas', EstadisticasView, basename='estadistica')
router.register(r'opciones', OpcionesView, basename='opciones')

# URLs del app
urlpatterns = [
    # Incluir todas las rutas del router
    path('api/', include(router.urls)),
    
    # Rutas adicionales específicas si se necesitan
    path('api/health/', lambda request: JsonResponse({'status': 'ok'}), name='health'),
]

# Importar JsonResponse para la ruta de health
from django.http import JsonResponse