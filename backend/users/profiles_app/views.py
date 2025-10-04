"""
Vistas para la aplicación de perfiles
Sistema Pontificia - Users Service
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import logging

from .services import ProfileService
from .serializers import (
    ProfileCreateSerializer, ProfileUpdateSerializer, 
    ProfileReadSerializer, ProfileListSerializer,
    SyncUserDataSerializer, ApiResponseSerializer
)

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profiles_view(request):
    """
    Vista principal para perfiles
    GET: Lista perfiles públicos
    POST: Crea un nuevo perfil
    """
    try:
        if request.method == 'GET':
            return listar_profiles(request)
        elif request.method == 'POST':
            return crear_profile(request)
    except Exception as e:
        logger.error(f"Error en profiles_view: {str(e)}")
        return Response({
            'exito': False,
            'mensaje': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_detail_view(request, usuario_id):
    """
    Vista para un perfil específico
    GET: Obtiene un perfil
    PUT: Actualiza un perfil
    """
    try:
        if request.method == 'GET':
            return obtener_profile(request, usuario_id)
        elif request.method == 'PUT':
            return actualizar_profile(request, usuario_id)
    except Exception as e:
        logger.error(f"Error en profile_detail_view: {str(e)}")
        return Response({
            'exito': False,
            'mensaje': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def listar_profiles(request):
    """
    Lista perfiles con filtros opcionales
    """
    try:
        # Obtener parámetros de consulta
        publicos_solo = request.GET.get('publicos', 'true').lower() == 'true'
        departamento = request.GET.get('departamento')
        
        # Llamar al servicio
        resultado = ProfileService.listar_profiles(publicos_solo, departamento)
        
        if resultado['exito']:
            # Serializar datos
            serializer = ProfileListSerializer(resultado['data'], many=True)
            
            return Response({
                'exito': True,
                'data': serializer.data,
                'total': resultado['total'],
                'filtros': {
                    'publicos_solo': publicos_solo,
                    'departamento': departamento
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'exito': False,
                'mensaje': resultado['mensaje']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error listando perfiles: {str(e)}")
        return Response({
            'exito': False,
            'mensaje': 'Error listando perfiles'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def crear_profile(request):
    """
    Crea un nuevo perfil
    """
    try:
        # Validar datos de entrada
        serializer = ProfileCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'exito': False,
                'mensaje': 'Datos inválidos',
                'errores': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener ID del usuario autenticado (simulado)
        # En producción, esto vendría del token JWT
        usuario_solicitante_id = getattr(request.user, 'id', None)
        
        # Llamar al servicio
        resultado = ProfileService.crear_profile(
            serializer.validated_data, 
            usuario_solicitante_id
        )
        
        if resultado['exito']:
            return Response(resultado, status=status.HTTP_201_CREATED)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error creando perfil: {str(e)}")
        return Response({
            'exito': False,
            'mensaje': 'Error creando perfil'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def obtener_profile(request, usuario_id):
    """
    Obtiene un perfil específico
    """
    try:
        # Validar usuario_id
        try:
            usuario_id = int(usuario_id)
        except ValueError:
            return Response({
                'exito': False,
                'mensaje': 'ID de usuario inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener ID del usuario autenticado
        solicitante_id = getattr(request.user, 'id', None)
        
        # Llamar al servicio
        resultado = ProfileService.obtener_profile(usuario_id, solicitante_id)
        
        if resultado['exito']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_404_NOT_FOUND if 'no encontrado' in resultado['mensaje'].lower() else status.HTTP_403_FORBIDDEN
            return Response(resultado, status=status_code)
            
    except Exception as e:
        logger.error(f"Error obteniendo perfil: {str(e)}")
        return Response({
            'exito': False,
            'mensaje': 'Error obteniendo perfil'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def actualizar_profile(request, usuario_id):
    """
    Actualiza un perfil específico
    """
    try:
        # Validar usuario_id
        try:
            usuario_id = int(usuario_id)
        except ValueError:
            return Response({
                'exito': False,
                'mensaje': 'ID de usuario inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar datos de entrada
        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'exito': False,
                'mensaje': 'Datos inválidos',
                'errores': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener ID del usuario autenticado
        solicitante_id = getattr(request.user, 'id', None)
        
        # Llamar al servicio
        resultado = ProfileService.actualizar_profile(
            usuario_id, 
            serializer.validated_data, 
            solicitante_id
        )
        
        if resultado['exito']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_404_NOT_FOUND if 'no encontrado' in resultado['mensaje'].lower() else status.HTTP_403_FORBIDDEN
            return Response(resultado, status=status_code)
            
    except Exception as e:
        logger.error(f"Error actualizando perfil: {str(e)}")
        return Response({
            'exito': False,
            'mensaje': 'Error actualizando perfil'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def estadisticas_view(request):
    """
    Vista para estadísticas de perfiles
    """
    try:
        estadisticas = ProfileService.obtener_estadisticas()
        
        return Response({
            'exito': True,
            'data': estadisticas
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return Response({
            'exito': False,
            'mensaje': 'Error obteniendo estadísticas'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def sync_profile_view(request):
    """
    Endpoint para sincronización con auth_service
    Este endpoint será llamado por auth_service cuando se cree un usuario
    """
    try:
        # Parsear datos JSON
        data = json.loads(request.body)
        
        # Validar datos
        serializer = SyncUserDataSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({
                'exito': False,
                'mensaje': 'Datos inválidos',
                'errores': serializer.errors
            }, status=400)
        
        # Llamar al servicio
        resultado = ProfileService.sincronizar_con_auth_service(
            serializer.validated_data['usuario_id'],
            serializer.validated_data
        )
        
        status_code = 201 if resultado.get('accion') == 'creado' else 200
        return JsonResponse(resultado, status=status_code)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'exito': False,
            'mensaje': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Error en sincronización: {str(e)}")
        return JsonResponse({
            'exito': False,
            'mensaje': 'Error en sincronización'
        }, status=500)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint para verificar el estado del servicio
    """
    try:
        # Verificar conexión a la base de datos
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return Response({
            'status': 'healthy',
            'service': 'users_service',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check falló: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
