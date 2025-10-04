"""
Views para la API REST del microservicio de autenticación
Sistema Pontificia - Auth Service
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Usuario
from .services import AuthService
from .serializers import (
    RegistrarUsuarioSerializer,
    LoginSerializer,
    TokenResponseSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    RefreshTokenResponseSerializer,
    CambiarPasswordSerializer,
    PerfilUsuarioSerializer,
    ActualizarPerfilSerializer,
    MensajeResponseSerializer,
    ErrorResponseSerializer
)

import logging
logger = logging.getLogger(__name__)


class RegistrarUsuarioView(APIView):
    """
    Endpoint para registrar un nuevo usuario en el sistema
    """
    
    @swagger_auto_schema(
        operation_description="Registrar un nuevo usuario en el sistema",
        request_body=RegistrarUsuarioSerializer,
        responses={
            201: openapi.Response(
                description="Usuario registrado exitosamente",
                schema=TokenResponseSerializer
            ),
            400: openapi.Response(
                description="Error en los datos enviados",
                schema=ErrorResponseSerializer
            )
        },
        tags=['Autenticación']
    )
    def post(self, request):
        """Registrar nuevo usuario"""
        try:
            serializer = RegistrarUsuarioSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'error': 'Datos inválidos',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar el servicio de autenticación
            resultado = AuthService.registrar_usuario(serializer.validated_data)
            
            if resultado['exito']:
                return Response(resultado['data'], status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': resultado['mensaje'],
                    'detail': resultado.get('errores', {})
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error registrando usuario: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    """
    Endpoint para autenticar usuarios
    """
    
    @swagger_auto_schema(
        operation_description="Autenticar usuario y obtener tokens JWT",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login exitoso",
                schema=TokenResponseSerializer
            ),
            401: openapi.Response(
                description="Credenciales inválidas",
                schema=ErrorResponseSerializer
            ),
            400: openapi.Response(
                description="Error en los datos enviados",
                schema=ErrorResponseSerializer
            )
        },
        tags=['Autenticación']
    )
    def post(self, request):
        """Autenticar usuario"""
        try:
            serializer = LoginSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'error': 'Datos inválidos',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar el servicio de autenticación
            resultado = AuthService.login(
                dni=serializer.validated_data['dni'],
                password=serializer.validated_data['password'],
                request=request
            )
            
            if resultado['exito']:
                return Response(resultado['data'], status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': resultado['mensaje']
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"Error en login: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    """
    Endpoint para cerrar sesión
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Cerrar sesión y revocar tokens",
        request_body=LogoutSerializer,
        responses={
            200: openapi.Response(
                description="Sesión cerrada exitosamente",
                schema=MensajeResponseSerializer
            ),
            400: openapi.Response(
                description="Error en los datos enviados",
                schema=ErrorResponseSerializer
            )
        },
        tags=['Autenticación']
    )
    def post(self, request):
        """Cerrar sesión"""
        try:
            serializer = LogoutSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'error': 'Datos inválidos',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar el servicio de autenticación
            resultado = AuthService.logout(
                usuario=request.user,
                refresh_token=serializer.validated_data['refresh_token'],
                request=request
            )
            
            if resultado['exito']:
                return Response({
                    'mensaje': resultado['mensaje'],
                    'exito': True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': resultado['mensaje']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error en logout: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshTokenView(APIView):
    """
    Endpoint para renovar tokens JWT
    """
    
    @swagger_auto_schema(
        operation_description="Renovar token de acceso usando refresh token",
        request_body=RefreshTokenSerializer,
        responses={
            200: openapi.Response(
                description="Token renovado exitosamente",
                schema=RefreshTokenResponseSerializer
            ),
            401: openapi.Response(
                description="Refresh token inválido",
                schema=ErrorResponseSerializer
            )
        },
        tags=['Autenticación']
    )
    def post(self, request):
        """Renovar token"""
        try:
            serializer = RefreshTokenSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'error': 'Datos inválidos',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar el servicio de autenticación
            resultado = AuthService.refresh_token(
                refresh_token=serializer.validated_data['refresh_token']
            )
            
            if resultado['exito']:
                return Response(resultado['data'], status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': resultado['mensaje']
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"Error renovando token: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerfilView(APIView):
    """
    Endpoint para obtener y actualizar el perfil del usuario
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Obtener perfil del usuario autenticado",
        responses={
            200: openapi.Response(
                description="Perfil obtenido exitosamente",
                schema=PerfilUsuarioSerializer
            )
        },
        tags=['Perfil']
    )
    def get(self, request):
        """Obtener perfil"""
        try:
            serializer = PerfilUsuarioSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo perfil: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_description="Actualizar perfil del usuario autenticado",
        request_body=ActualizarPerfilSerializer,
        responses={
            200: openapi.Response(
                description="Perfil actualizado exitosamente",
                schema=PerfilUsuarioSerializer
            ),
            400: openapi.Response(
                description="Error en los datos enviados",
                schema=ErrorResponseSerializer
            )
        },
        tags=['Perfil']
    )
    def put(self, request):
        """Actualizar perfil"""
        try:
            serializer = ActualizarPerfilSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            
            if not serializer.is_valid():
                return Response({
                    'error': 'Datos inválidos',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            usuario_actualizado = serializer.save()
            usuario_actualizado.fecha_modificacion = timezone.now()
            usuario_actualizado.save()
            
            return Response(
                PerfilUsuarioSerializer(usuario_actualizado).data,
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error actualizando perfil: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CambiarPasswordView(APIView):
    """
    Endpoint para cambiar contraseña
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Cambiar contraseña del usuario autenticado",
        request_body=CambiarPasswordSerializer,
        responses={
            200: openapi.Response(
                description="Contraseña cambiada exitosamente",
                schema=MensajeResponseSerializer
            ),
            400: openapi.Response(
                description="Error en los datos enviados",
                schema=ErrorResponseSerializer
            )
        },
        tags=['Perfil']
    )
    def post(self, request):
        """Cambiar contraseña"""
        try:
            serializer = CambiarPasswordSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'error': 'Datos inválidos',
                    'detail': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar contraseña actual
            usuario = request.user
            if not usuario.check_password(serializer.validated_data['password_actual']):
                return Response({
                    'error': 'Contraseña actual incorrecta'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Cambiar contraseña
            usuario.set_password(serializer.validated_data['password_nueva'])
            usuario.fecha_modificacion = timezone.now()
            usuario.save()
            
            logger.info(f"Contraseña cambiada para usuario {usuario.dni}")
            
            return Response({
                'mensaje': 'Contraseña cambiada exitosamente',
                'exito': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error cambiando contraseña: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutAllView(APIView):
    """
    Endpoint para cerrar todas las sesiones del usuario
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Cerrar todas las sesiones del usuario autenticado",
        responses={
            200: openapi.Response(
                description="Todas las sesiones cerradas exitosamente",
                schema=MensajeResponseSerializer
            )
        },
        tags=['Autenticación']
    )
    def post(self, request):
        """Cerrar todas las sesiones"""
        try:
            # Cerrar todas las sesiones del usuario
            from .models import SesionUsuario
            sesiones_cerradas = SesionUsuario.objects.filter(
                usuario=request.user,
                activa=True
            ).update(
                activa=False,
                fecha_fin=timezone.now()
            )
            
            logger.info(f"Sesiones cerradas para usuario {request.user.dni}: {sesiones_cerradas}")
            
            return Response({
                'mensaje': f'Se cerraron {sesiones_cerradas} sesiones activas',
                'exito': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error cerrando todas las sesiones: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_description="Verificar el estado de salud del servicio de autenticación",
    responses={
        200: openapi.Response(
            description="Servicio funcionando correctamente",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING),
                    'version': openapi.Schema(type=openapi.TYPE_STRING),
                    'database': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    tags=['Health Check']
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """
    Endpoint de health check para verificar el estado del servicio
    """
    try:
        # Verificar conexión a la base de datos
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    return Response({
        'status': 'OK' if db_status == 'OK' else 'DEGRADED',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'database': db_status,
        'service': 'auth-service',
        'port': 3001
    }, status=status.HTTP_200_OK)
