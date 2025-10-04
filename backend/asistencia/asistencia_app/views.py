from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

from .services import AsistenciaService, JustificacionService
from .serializers import (
    RegistrarAsistenciaSerializer, ActualizarSalidaSerializer,
    HistorialAsistenciaSerializer, MarcarAusenciaSerializer,
    CrearJustificacionSerializer, ProcesarJustificacionSerializer,
    EstadisticasAsistenciaSerializer, CambiarEstrategiaSerializer,
    RespuestaRegistroSerializer, RespuestaHistorialSerializer,
    RespuestaJustificacionSerializer, RespuestaEstadisticasSerializer,
    RegistroHoraSerializer, JustificacionAusenciaSerializer
)

logger = logging.getLogger(__name__)

class RegistrarAsistenciaView(APIView):
    """Vista para registrar asistencia - POST /api/asistencia/registrar"""
    
    def __init__(self):
        super().__init__()
        self.asistencia_service = AsistenciaService()
    
    def post(self, request):
        """Registra la asistencia de un docente"""
        try:
            serializer = RegistrarAsistenciaSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Registrar asistencia usando el service
            registro = self.asistencia_service.registrar_asistencia(
                docente_id=validated_data['docente_id'],
                aula=validated_data['aula'],
                seccion=validated_data['seccion'],
                hora_entrada=validated_data.get('hora_entrada')
            )
            
            # Preparar respuesta
            registro_serializer = RegistroHoraSerializer(registro)
            
            return Response({
                'success': True,
                'message': f'Asistencia registrada exitosamente - Estado: {registro.estado}',
                'data': registro_serializer.data,
                'descuento_aplicado': float(registro.descuento_aplicado),
                'minutos_tardanza': registro.minutos_tardanza
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error en RegistrarAsistenciaView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ActualizarSalidaView(APIView):
    """Vista para actualizar hora de salida - PUT /api/asistencia/actualizar-salida"""
    
    def __init__(self):
        super().__init__()
        self.asistencia_service = AsistenciaService()
    
    def put(self, request):
        """Actualiza la hora de salida de un registro"""
        try:
            serializer = ActualizarSalidaSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Actualizar salida
            registro = self.asistencia_service.actualizar_salida(
                registro_id=validated_data['registro_id'],
                hora_salida=validated_data.get('hora_salida')
            )
            
            if not registro:
                return Response({
                    'success': False,
                    'message': 'Registro no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            registro_serializer = RegistroHoraSerializer(registro)
            
            return Response({
                'success': True,
                'message': 'Hora de salida actualizada exitosamente',
                'data': registro_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en ActualizarSalidaView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HistorialAsistenciaView(APIView):
    """Vista para obtener historial - GET /api/asistencia/historial"""
    
    def __init__(self):
        super().__init__()
        self.asistencia_service = AsistenciaService()
    
    def get(self, request):
        """Obtiene el historial de asistencia de un docente"""
        try:
            # Obtener parámetros de query
            docente_id = request.query_params.get('docente_id')
            fecha_inicio = request.query_params.get('fecha_inicio')
            fecha_fin = request.query_params.get('fecha_fin')
            
            if not docente_id:
                return Response({
                    'success': False,
                    'message': 'El parámetro docente_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear data para serializer
            query_data = {'docente_id': docente_id}
            if fecha_inicio:
                query_data['fecha_inicio'] = fecha_inicio
            if fecha_fin:
                query_data['fecha_fin'] = fecha_fin
            
            serializer = HistorialAsistenciaSerializer(data=query_data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Parámetros inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Obtener historial
            registros = self.asistencia_service.obtener_historial_docente(
                docente_id=validated_data['docente_id'],
                fecha_inicio=validated_data.get('fecha_inicio'),
                fecha_fin=validated_data.get('fecha_fin')
            )
            
            registros_serializer = RegistroHoraSerializer(registros, many=True)
            
            return Response({
                'success': True,
                'message': 'Historial obtenido exitosamente',
                'data': registros_serializer.data,
                'total_registros': len(registros)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en HistorialAsistenciaView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarcarAusenciaView(APIView):
    """Vista para marcar ausencia - POST /api/asistencia/marcar-ausencia"""
    
    def __init__(self):
        super().__init__()
        self.asistencia_service = AsistenciaService()
    
    def post(self, request):
        """Marca ausencia para un docente"""
        try:
            serializer = MarcarAusenciaSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Marcar ausencia
            registro = self.asistencia_service.marcar_ausencia(
                docente_id=validated_data['docente_id'],
                fecha=validated_data['fecha'],
                observacion=validated_data.get('observacion')
            )
            
            registro_serializer = RegistroHoraSerializer(registro)
            
            return Response({
                'success': True,
                'message': 'Ausencia marcada exitosamente',
                'data': registro_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error en MarcarAusenciaView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CrearJustificacionView(APIView):
    """Vista para crear justificación - POST /api/asistencia/justificacion"""
    
    def __init__(self):
        super().__init__()
        self.justificacion_service = JustificacionService()
    
    def post(self, request):
        """Crea una nueva justificación de ausencia"""
        try:
            serializer = CrearJustificacionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Crear justificación
            justificacion = self.justificacion_service.crear_justificacion(
                docente_id=validated_data['docente_id'],
                fecha=validated_data['fecha'],
                motivo=validated_data['motivo'],
                tipo_motivo=validated_data.get('tipo_motivo', 'OTROS'),
                documentos_adjuntos=validated_data.get('documentos_adjuntos')
            )
            
            justificacion_serializer = JustificacionAusenciaSerializer(justificacion)
            
            return Response({
                'success': True,
                'message': 'Justificación creada exitosamente',
                'data': justificacion_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error en CrearJustificacionView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProcesarJustificacionView(APIView):
    """Vista para procesar justificación - PUT /api/asistencia/justificacion/{id}/procesar"""
    
    def __init__(self):
        super().__init__()
        self.justificacion_service = JustificacionService()
    
    def put(self, request, justificacion_id):
        """Procesa (aprueba o rechaza) una justificación"""
        try:
            serializer = ProcesarJustificacionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Procesar justificación
            justificacion = self.justificacion_service.procesar_justificacion(
                justificacion_id=justificacion_id,
                accion=validated_data['accion'],
                revisor_id=validated_data['revisor_id'],
                comentario_revisor=validated_data.get('comentario_revisor')
            )
            
            justificacion_serializer = JustificacionAusenciaSerializer(justificacion)
            
            return Response({
                'success': True,
                'message': f'Justificación {validated_data["accion"].lower()}ada exitosamente',
                'data': justificacion_serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error en ProcesarJustificacionView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JustificacionesDocenteView(APIView):
    """Vista para obtener justificaciones de un docente - GET /api/asistencia/justificaciones"""
    
    def __init__(self):
        super().__init__()
        self.justificacion_service = JustificacionService()
    
    def get(self, request):
        """Obtiene las justificaciones de un docente"""
        try:
            docente_id = request.query_params.get('docente_id')
            fecha_inicio = request.query_params.get('fecha_inicio')
            fecha_fin = request.query_params.get('fecha_fin')
            
            if not docente_id:
                return Response({
                    'success': False,
                    'message': 'El parámetro docente_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener justificaciones
            justificaciones = self.justificacion_service.obtener_justificaciones_docente(
                docente_id=int(docente_id),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            justificaciones_serializer = JustificacionAusenciaSerializer(justificaciones, many=True)
            
            return Response({
                'success': True,
                'message': 'Justificaciones obtenidas exitosamente',
                'data': justificaciones_serializer.data,
                'total_justificaciones': len(justificaciones)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en JustificacionesDocenteView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EstadisticasAsistenciaView(APIView):
    """Vista para obtener estadísticas - GET /api/asistencia/estadisticas"""
    
    def __init__(self):
        super().__init__()
        self.asistencia_service = AsistenciaService()
    
    def get(self, request):
        """Obtiene estadísticas de asistencia de un docente"""
        try:
            docente_id = request.query_params.get('docente_id')
            fecha_inicio = request.query_params.get('fecha_inicio')
            fecha_fin = request.query_params.get('fecha_fin')
            
            if not docente_id:
                return Response({
                    'success': False,
                    'message': 'El parámetro docente_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            query_data = {'docente_id': docente_id}
            if fecha_inicio:
                query_data['fecha_inicio'] = fecha_inicio
            if fecha_fin:
                query_data['fecha_fin'] = fecha_fin
            
            serializer = EstadisticasAsistenciaSerializer(data=query_data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Parámetros inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Obtener estadísticas
            estadisticas = self.asistencia_service.obtener_estadisticas_docente(
                docente_id=validated_data['docente_id'],
                fecha_inicio=validated_data.get('fecha_inicio'),
                fecha_fin=validated_data.get('fecha_fin')
            )
            
            return Response({
                'success': True,
                'message': 'Estadísticas obtenidas exitosamente',
                'data': estadisticas
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en EstadisticasAsistenciaView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CambiarEstrategiaView(APIView):
    """Vista para cambiar estrategia de descuento - POST /api/asistencia/cambiar-estrategia"""
    
    def __init__(self):
        super().__init__()
        self.asistencia_service = AsistenciaService()
    
    def post(self, request):
        """Cambia la estrategia de cálculo de descuentos"""
        try:
            serializer = CambiarEstrategiaSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Cambiar estrategia
            self.asistencia_service.cambiar_estrategia_descuento(
                validated_data['tipo_estrategia']
            )
            
            return Response({
                'success': True,
                'message': f'Estrategia cambiada a: {validated_data["tipo_estrategia"]}'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en CambiarEstrategiaView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
