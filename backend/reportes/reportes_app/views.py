"""
Views/Endpoints para el microservicio de reportes
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .models import Reporte, Metrica, ReporteMetrica
from .services import ReporteService, MetricaService
from .repositories import ReporteRepository, MetricaRepository
from .serializers import (
    CrearReporteSerializer, ReporteSerializer, ReporteResumenSerializer,
    MetricaSerializer, ExportarMetricasSerializer, EstadisticasReporteSerializer,
    RespuestaReporteSerializer, ErrorReporteSerializer
)
from .exceptions import (
    ReporteNoEncontradoException, FormatoNoSoportadoException,
    ParametrosInvalidosException, ErrorProcesamiento
)

logger = logging.getLogger(__name__)


# ========== Paginación ==========

class ReportePagination(PageNumberPagination):
    """Paginación personalizada para reportes"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ========== ViewSets ==========

class ReporteViewSet(ModelViewSet):
    """
    ViewSet completo para gestión de reportes
    
    list: Obtener lista de reportes del usuario
    create: Generar un nuevo reporte
    retrieve: Obtener detalles de un reporte específico
    destroy: Eliminar un reporte (soft delete)
    """
    
    serializer_class = ReporteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ReportePagination
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reporte_service = ReporteService()
        self.reporte_repository = ReporteRepository()
    
    def get_queryset(self):
        """Filtrar reportes por usuario y parámetros de consulta"""
        queryset = self.reporte_repository.obtener_por_autor(self.request.user.id)
        
        # Filtros opcionales
        tipo = self.request.query_params.get('tipo')
        estado = self.request.query_params.get('estado')
        formato = self.request.query_params.get('formato')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if formato:
            queryset = queryset.filter(formato=formato)
        if fecha_desde:
            try:
                fecha = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__date__gte=fecha)
            except ValueError:
                pass
        if fecha_hasta:
            try:
                fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__date__lte=fecha)
            except ValueError:
                pass
        
        return queryset.order_by('-fecha_creacion')
    
    def get_serializer_class(self):
        """Usar serializer resumido para listados"""
        if self.action == 'list':
            return ReporteResumenSerializer
        return ReporteSerializer
    
    def create(self, request):
        """Generar un nuevo reporte"""
        try:
            serializer = CrearReporteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Datos inválidos', 'detalles': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            
            # Generar reporte usando el servicio
            if data.get('asincrono', True):
                # Procesamiento asíncrono
                reporte = self.reporte_service.generar_reporte_async(
                    tipo=data['tipo'],
                    formato=data['formato'],
                    parametros=data.get('parametros', {}),
                    autor_id=request.user.id,
                    titulo=data.get('titulo')
                )
                
                response_data = {
                    'success': True,
                    'message': 'Reporte iniciado correctamente',
                    'reporte_id': reporte.id,
                    'estado': reporte.estado,
                    'url_seguimiento': f'/api/reportes/{reporte.id}/',
                    'tiempo_estimado': self._estimar_tiempo_procesamiento(data['tipo'])
                }
                
                return Response(
                    RespuestaReporteSerializer(response_data).data,
                    status=status.HTTP_202_ACCEPTED
                )
            else:
                # Procesamiento síncrono
                reporte = self.reporte_service.generar_reporte_sync(
                    tipo=data['tipo'],
                    formato=data['formato'],
                    parametros=data.get('parametros', {}),
                    autor_id=request.user.id,
                    titulo=data.get('titulo')
                )
                
                serializer = ReporteSerializer(reporte, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ParametrosInvalidosException as e:
            return Response(
                ErrorReporteSerializer({
                    'error': e.message,
                    'codigo': e.error_code
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al generar reporte: {str(e)}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Obtener detalles de un reporte específico"""
        try:
            reporte = self.reporte_repository.obtener_por_id(pk)
            
            # Verificar permisos
            if reporte.autor_id != request.user.id:
                return Response(
                    {'error': 'No tienes permisos para ver este reporte'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ReporteSerializer(reporte, context={'request': request})
            return Response(serializer.data)
        
        except ReporteNoEncontradoException:
            return Response(
                {'error': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def destroy(self, request, pk=None):
        """Eliminar un reporte (soft delete)"""
        try:
            reporte = self.reporte_repository.obtener_por_id(pk)
            
            # Verificar permisos
            if reporte.autor_id != request.user.id:
                return Response(
                    {'error': 'No tienes permisos para eliminar este reporte'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            self.reporte_service.eliminar_reporte(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except ReporteNoEncontradoException:
            return Response(
                {'error': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        """Descargar archivo de reporte"""
        try:
            reporte = self.reporte_repository.obtener_por_id(pk)
            
            # Verificar permisos
            if reporte.autor_id != request.user.id:
                return Response(
                    {'error': 'No tienes permisos para descargar este reporte'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verificar que el reporte esté completado
            if reporte.estado != 'completado':
                return Response(
                    {'error': 'El reporte aún no está listo para descarga'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar que el archivo exista
            if not reporte.archivo:
                return Response(
                    {'error': 'Archivo de reporte no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar expiración
            if reporte.esta_expirado():
                return Response(
                    {'error': 'El reporte ha expirado'},
                    status=status.HTTP_410_GONE
                )
            
            # Servir archivo
            response = FileResponse(
                reporte.archivo.open('rb'),
                as_attachment=True,
                filename=f"reporte_{reporte.id}.{reporte.formato}"
            )
            
            return response
        
        except ReporteNoEncontradoException:
            return Response(
                {'error': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al descargar reporte {pk}: {str(e)}")
            return Response(
                {'error': 'Error al descargar archivo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def regenerar(self, request, pk=None):
        """Regenerar un reporte existente"""
        try:
            reporte_original = self.reporte_repository.obtener_por_id(pk)
            
            # Verificar permisos
            if reporte_original.autor_id != request.user.id:
                return Response(
                    {'error': 'No tienes permisos para regenerar este reporte'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Regenerar usando los mismos parámetros
            nuevo_reporte = self.reporte_service.generar_reporte_async(
                tipo=reporte_original.tipo,
                formato=reporte_original.formato,
                parametros=reporte_original.parametros,
                autor_id=request.user.id,
                titulo=f"Regenerado: {reporte_original.titulo}"
            )
            
            response_data = {
                'success': True,
                'message': 'Reporte regenerado correctamente',
                'reporte_id': nuevo_reporte.id,
                'estado': nuevo_reporte.estado,
                'url_seguimiento': f'/api/reportes/{nuevo_reporte.id}/'
            }
            
            return Response(
                RespuestaReporteSerializer(response_data).data,
                status=status.HTTP_202_ACCEPTED
            )
        
        except ReporteNoEncontradoException:
            return Response(
                {'error': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al regenerar reporte {pk}: {str(e)}")
            return Response(
                {'error': 'Error al regenerar reporte'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _estimar_tiempo_procesamiento(self, tipo_reporte: str) -> int:
        """Estima tiempo de procesamiento en segundos"""
        tiempos = {
            'ventas': 30,
            'usuarios': 15,
            'metricas': 45,
            'financiero': 60,
            'academico': 40,
            'asistencia': 20,
            'calificaciones': 35,
            'personalizado': 90
        }
        return tiempos.get(tipo_reporte, 30)


class MetricaViewSet(ModelViewSet):
    """
    ViewSet para gestión de métricas
    """
    
    serializer_class = MetricaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ReportePagination
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrica_service = MetricaService()
        self.metrica_repository = MetricaRepository()
    
    def get_queryset(self):
        """Obtener métricas con filtros"""
        queryset = self.metrica_repository.obtener_activas()
        
        # Filtros
        nombre = self.request.query_params.get('nombre')
        periodo = self.request.query_params.get('periodo')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        if fecha_desde:
            try:
                fecha = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_calculo__date__gte=fecha)
            except ValueError:
                pass
        if fecha_hasta:
            try:
                fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_calculo__date__lte=fecha)
            except ValueError:
                pass
        
        return queryset.order_by('-fecha_calculo')
    
    @action(detail=False, methods=['post'])
    def exportar(self, request):
        """Exportar métricas en diferentes formatos"""
        try:
            serializer = ExportarMetricasSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Parámetros inválidos', 'detalles': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            
            # Exportar métricas
            archivo_path = self.metrica_service.exportar_metricas(
                nombres=data.get('nombres'),
                periodo=data.get('periodo'),
                fecha_desde=data.get('fecha_desde'),
                fecha_hasta=data.get('fecha_hasta'),
                formato=data.get('formato', 'excel'),
                incluir_graficos=data.get('incluir_graficos', True),
                solo_activas=data.get('solo_activas', True)
            )
            
            # Servir archivo
            with open(archivo_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="metricas_export.{data.get("formato", "excel")}"'
                return response
        
        except Exception as e:
            logger.error(f"Error al exportar métricas: {str(e)}")
            return Response(
                {'error': 'Error al exportar métricas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtener resumen de métricas"""
        try:
            periodo = request.query_params.get('periodo', 'mensual')
            resumen = self.metrica_service.obtener_resumen_metricas(periodo)
            return Response(resumen)
        
        except Exception as e:
            logger.error(f"Error al obtener resumen de métricas: {str(e)}")
            return Response(
                {'error': 'Error al obtener resumen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ========== API Views ==========

class EstadisticasReportesView(APIView):
    """
    Vista para obtener estadísticas de reportes
    """
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reporte_repository = ReporteRepository()
    
    def get(self, request):
        """Obtener estadísticas de reportes del usuario"""
        try:
            # Obtener reportes del usuario
            reportes = self.reporte_repository.obtener_por_autor(request.user.id)
            
            # Calcular estadísticas
            total_reportes = reportes.count()
            reportes_completados = reportes.filter(estado='completado').count()
            reportes_pendientes = reportes.filter(estado__in=['pendiente', 'procesando']).count()
            reportes_error = reportes.filter(estado='error').count()
            
            # Tiempo promedio de procesamiento
            reportes_con_tiempo = reportes.filter(
                estado='completado',
                fecha_actualizacion__isnull=False
            )
            
            tiempo_promedio = 0
            if reportes_con_tiempo.exists():
                tiempos = [
                    (r.fecha_actualizacion - r.fecha_creacion).total_seconds()
                    for r in reportes_con_tiempo
                ]
                tiempo_promedio = sum(tiempos) / len(tiempos)
            
            # Tipos más solicitados
            tipos_count = reportes.values('tipo').annotate(
                count=Count('tipo')
            ).order_by('-count')[:5]
            tipos_mas_solicitados = [
                {'tipo': item['tipo'], 'cantidad': item['count']}
                for item in tipos_count
            ]
            
            # Formatos preferidos
            formatos_count = reportes.values('formato').annotate(
                count=Count('formato')
            )
            formatos_preferidos = {
                item['formato']: item['count']
                for item in formatos_count
            }
            
            estadisticas = {
                'total_reportes': total_reportes,
                'reportes_completados': reportes_completados,
                'reportes_pendientes': reportes_pendientes,
                'reportes_error': reportes_error,
                'tiempo_promedio_procesamiento': tiempo_promedio,
                'tipos_mas_solicitados': tipos_mas_solicitados,
                'formatos_preferidos': formatos_preferidos
            }
            
            serializer = EstadisticasReporteSerializer(estadisticas)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return Response(
                {'error': 'Error al obtener estadísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EstadoReporteView(APIView):
    """
    Vista para consultar el estado de un reporte específico
    """
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reporte_repository = ReporteRepository()
    
    def get(self, request, reporte_id):
        """Obtener estado actual del reporte"""
        try:
            reporte = self.reporte_repository.obtener_por_id(reporte_id)
            
            # Verificar permisos
            if reporte.autor_id != request.user.id:
                return Response(
                    {'error': 'No tienes permisos para ver este reporte'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Información del estado
            estado_info = {
                'id': reporte.id,
                'estado': reporte.estado,
                'estado_display': reporte.get_estado_display(),
                'progreso': self._calcular_progreso(reporte),
                'fecha_creacion': reporte.fecha_creacion,
                'fecha_actualizacion': reporte.fecha_actualizacion,
                'tiempo_transcurrido': (timezone.now() - reporte.fecha_creacion).total_seconds(),
                'archivo_disponible': bool(reporte.archivo),
                'expirado': reporte.esta_expirado(),
                'url_descarga': None
            }
            
            # URL de descarga si está disponible
            if reporte.archivo and reporte.estado == 'completado':
                estado_info['url_descarga'] = request.build_absolute_uri(
                    f'/api/reportes/{reporte.id}/descargar/'
                )
            
            return Response(estado_info)
        
        except ReporteNoEncontradoException:
            return Response(
                {'error': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al obtener estado del reporte {reporte_id}: {str(e)}")
            return Response(
                {'error': 'Error al obtener estado'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calcular_progreso(self, reporte) -> int:
        """Calcula el progreso del reporte en porcentaje"""
        estado_progreso = {
            'pendiente': 0,
            'procesando': 50,
            'completado': 100,
            'error': 0
        }
        return estado_progreso.get(reporte.estado, 0)


# ========== API Functions ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_reporte(request):
    """
    Endpoint para generar reportes (función simple)
    
    POST /api/reportes/generar/
    """
    try:
        serializer = CrearReporteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Datos inválidos', 'detalles': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        reporte_service = ReporteService()
        
        # Generar reporte asíncrono por defecto
        reporte = reporte_service.generar_reporte_async(
            tipo=data['tipo'],
            formato=data['formato'],
            parametros=data.get('parametros', {}),
            autor_id=request.user.id,
            titulo=data.get('titulo')
        )
        
        response_data = {
            'success': True,
            'message': 'Reporte iniciado correctamente',
            'reporte_id': reporte.id,
            'estado': reporte.estado,
            'url_seguimiento': f'/api/reportes/{reporte.id}/'
        }
        
        return Response(
            RespuestaReporteSerializer(response_data).data,
            status=status.HTTP_202_ACCEPTED
        )
    
    except Exception as e:
        logger.error(f"Error al generar reporte: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_reportes(request):
    """
    Endpoint para listar reportes del usuario
    
    GET /api/reportes/listar/
    """
    try:
        reporte_repository = ReporteRepository()
        reportes = reporte_repository.obtener_por_autor(request.user.id)
        
        # Aplicar filtros
        tipo = request.query_params.get('tipo')
        estado = request.query_params.get('estado')
        
        if tipo:
            reportes = reportes.filter(tipo=tipo)
        if estado:
            reportes = reportes.filter(estado=estado)
        
        # Paginación
        paginator = ReportePagination()
        page = paginator.paginate_queryset(reportes, request)
        
        if page is not None:
            serializer = ReporteResumenSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ReporteResumenSerializer(reportes, many=True)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error al listar reportes: {str(e)}")
        return Response(
            {'error': 'Error al obtener reportes'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """
    Endpoint de verificación de salud del servicio
    """
    try:
        # Verificar conexión a base de datos
        from django.db import connection
        connection.ensure_connection()
        
        # Verificar Celery (opcional)
        celery_status = 'desconocido'
        try:
            from .tasks import test_celery
            result = test_celery.delay()
            celery_status = 'activo' if result else 'inactivo'
        except:
            celery_status = 'inactivo'
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'database': 'connected',
            'celery': celery_status,
            'version': '1.0.0'
        })
    
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
