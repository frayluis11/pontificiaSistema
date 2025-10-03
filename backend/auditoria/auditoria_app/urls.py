"""
URLs para el microservicio de auditoría
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'logs', views.ActividadSistemaViewSet, basename='logs')

# Patrones de URL
urlpatterns = [
    # API REST
    path('api/', include(router.urls)),
    
    # Webhooks para recibir notificaciones de otros microservicios
    path('api/webhooks/documents/', views.WebhookDocumentView.as_view(), name='webhook-documents'),
    path('api/webhooks/payments/', views.WebhookPaymentView.as_view(), name='webhook-payments'),
    path('api/webhooks/users/', views.WebhookUserView.as_view(), name='webhook-users'),
    path('api/webhooks/attendance/', views.WebhookAttendanceView.as_view(), name='webhook-attendance'),
    path('api/webhooks/generic/', views.WebhookGenericView.as_view(), name='webhook-generic'),
    
    # Health check y system info
    path('api/health/', views.health_check, name='health-check'),
    path('api/system-info/', views.system_info, name='system-info'),
]

# Patrones adicionales para endpoints específicos de logs
logs_patterns = [
    # GET /api/logs/ - Listar logs con filtros
    # GET /api/logs/{id}/ - Detalle de un log específico
    # GET /api/logs/estadisticas/ - Estadísticas de auditoría
    # GET /api/logs/actividad_sospechosa/ - Actividades sospechosas
    # GET /api/logs/exportar_csv/ - Exportar a CSV
    # GET /api/logs/exportar_excel/ - Exportar a Excel  
    # GET /api/logs/exportar_pdf/ - Exportar a PDF
    # GET /api/logs/metricas_rendimiento/ - Métricas de rendimiento (admin)
    # POST /api/logs/limpiar_logs_antiguos/ - Limpiar logs antiguos (admin)
]