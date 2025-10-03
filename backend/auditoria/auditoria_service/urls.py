"""
URL configuration for auditoria_service project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def root_view(request):
    """Vista raíz del microservicio de auditoría"""
    return JsonResponse({
        'microservice': 'auditoria',
        'version': '1.0.0',
        'status': 'running',
        'port': 3007,
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/',
            'health': '/api/health/',
            'logs': '/api/logs/',
            'webhooks': {
                'documents': '/api/webhooks/documents/',
                'payments': '/api/webhooks/payments/',
                'users': '/api/webhooks/users/',
                'attendance': '/api/webhooks/attendance/',
                'generic': '/api/webhooks/generic/'
            }
        }
    })

urlpatterns = [
    # Vista raíz
    path('', root_view, name='root'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API de auditoría
    path('', include('auditoria_app.urls')),
]
