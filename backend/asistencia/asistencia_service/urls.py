"""
URL configuration for asistencia_service project.

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
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint para verificar que el servicio está funcionando"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'asistencia_service',
        'version': '1.0.0'
    })

def service_info(request):
    """Información del servicio"""
    return JsonResponse({
        'service': 'Sistema Pontificia - Servicio de Asistencia',
        'version': '1.0.0',
        'description': 'Microservicio para gestión de asistencia y justificaciones de docentes',
        'endpoints': {
            'asistencia': '/api/asistencia/',
            'admin': '/admin/',
            'health': '/health/',
        }
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    path('', service_info, name='service_info'),
    
    # API endpoints
    path('api/asistencia/', include('asistencia_app.urls')),
]
