"""
URL configuration for reportes_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone

def home_view(request):
    """Vista principal del microservicio de reportes"""
    return JsonResponse({
        'service': 'Microservicio de Reportes',
        'version': '1.0.0',
        'status': 'active',
        'timestamp': timezone.now().isoformat(),
        'description': 'Servicio para generación y gestión de reportes',
        'endpoints': {
            'health': '/api/health/',
            'reportes': '/api/reportes/',
            'metricas': '/api/metricas/',
            'generar': '/api/reportes/generar/',
            'listar': '/api/reportes/listar/',
            'estadisticas': '/api/estadisticas/',
            'admin': '/admin/'
        }
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Vista principal
    path('', home_view, name='home'),
    
    # URLs de la aplicación
    path('', include('reportes_app.urls')),
    
    # API de autenticación (si necesitas)
    # path('api/auth/', include('rest_framework.urls')),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
