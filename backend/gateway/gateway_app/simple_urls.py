"""
URLs simplificadas para el API Gateway
"""

from django.urls import path, include
from . import simple_views

app_name = 'gateway_app'

urlpatterns = [
    # Endpoints básicos
    path('', simple_views.root_view, name='root'),
    path('health/', simple_views.health_check, name='health'),
    path('docs/', simple_views.docs_view, name='docs'),
    path('api/gateway/', simple_views.gateway_info, name='gateway_info'),
    
    # Proxy endpoints para microservicios
    path('api/auth/<path:path>', simple_views.proxy_auth, name='proxy_auth'),
    path('api/users/<path:path>', simple_views.proxy_users, name='proxy_users'),
    path('api/asistencia/<path:path>', simple_views.proxy_asistencia, name='proxy_asistencia'),
    path('api/documentos/<path:path>', simple_views.proxy_documentos, name='proxy_documentos'),
    path('api/pagos/<path:path>', simple_views.proxy_pagos, name='proxy_pagos'),
    path('api/reportes/<path:path>', simple_views.proxy_reportes, name='proxy_reportes'),
    path('api/auditoria/<path:path>', simple_views.proxy_auditoria, name='proxy_auditoria'),
]