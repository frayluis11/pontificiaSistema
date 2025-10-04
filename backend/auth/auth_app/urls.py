"""
URLs para el microservicio AUTH - Sistema Pontificia
"""
from django.urls import path
from . import views

app_name = 'auth_app'

urlpatterns = [
    # Endpoints de autenticación
    path('register/', views.RegistrarUsuarioView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh'),
    
    # Endpoints de perfil
    path('profile/', views.PerfilView.as_view(), name='profile'),
    path('change-password/', views.CambiarPasswordView.as_view(), name='change-password'),
    path('logout-all/', views.LogoutAllView.as_view(), name='logout-all'),
    
    # Health check
    path('health/', views.health_check, name='health-check'),
]
