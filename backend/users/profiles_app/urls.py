"""
URLs para la aplicación de perfiles
Sistema Pontificia - Users Service
"""
from django.urls import path
from . import views
from .test_views import test_view

app_name = 'profiles'

urlpatterns = [
    # Test endpoint
    path('test/', test_view, name='test'),
    
    # Endpoints principales de perfiles
    path('profiles/', views.profiles_view, name='profiles'),
    path('profiles/<int:usuario_id>/', views.profile_detail_view, name='profile_detail'),
    
    # Endpoints de utilidad
    path('estadisticas/', views.estadisticas_view, name='estadisticas'),
    path('health/', views.health_check, name='health_check'),
    
    # Endpoint para sincronización con auth_service
    path('sync/', views.sync_profile_view, name='sync_profile'),
]
