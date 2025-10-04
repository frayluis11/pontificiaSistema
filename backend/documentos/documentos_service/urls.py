"""
URL configuration for documentos_service project.

Configuración principal de URLs para el servicio de documentos
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def health_check(request):
    """Endpoint de verificación de salud del servicio"""
    return JsonResponse({
        'service': 'documentos',
        'status': 'healthy',
        'version': '1.0.0',
        'port': 3004
    })


urlpatterns = [
    # Administración de Django
    path('admin/', admin.site.urls),
    
    # Endpoint de salud
    path('health/', health_check, name='health'),
    
    # API de documentos
    path('', include('documentos_app.urls')),
    
    # Documentación de la API con drf-spectacular
    path('api/schema/', include([
        path('', lambda r: JsonResponse({'message': 'API Schema disponible en /api/docs/'})),
    ])),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
