"""
URLs del microservicio de reportes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'reportes', views.ReporteViewSet, basename='reporte')
router.register(r'metricas', views.MetricaViewSet, basename='metrica')

app_name = 'reportes_app'

urlpatterns = [
    # URLs del router (ViewSets)
    path('api/', include(router.urls)),
    
    # URLs adicionales (funciones)
    path('api/reportes/generar/', views.generar_reporte, name='generar_reporte'),
    path('api/reportes/listar/', views.listar_reportes, name='listar_reportes'),
    
    # URLs de estado y estadísticas
    path('api/reportes/<str:reporte_id>/estado/', views.EstadoReporteView.as_view(), name='estado_reporte'),
    path('api/estadisticas/', views.EstadisticasReportesView.as_view(), name='estadisticas_reportes'),
    
    # Health check
    path('api/health/', views.health_check, name='health_check'),
]