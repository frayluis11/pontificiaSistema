"""
Vistas para el microservicio de pagos

Contiene todos los endpoints REST para la gestión de pagos,
planillas, boletas y adelantos.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend  # Comentado temporalmente
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from decimal import Decimal
import logging

from .models import (
    Pago, Planilla, Boleta, Adelanto, Descuento, 
    Bonificacion, PagoDescuento, PagoBonificacion
)
from .serializers import (
    PagoSerializer, PlanillaSerializer, BoletaSerializer, AdelantoSerializer,
    DescuentoSerializer, BonificacionSerializer, GenerarPlanillaSerializer,
    AprobarPlanillaSerializer, GenerarBoletaSerializer, AprobarAdelantoSerializer,
    RechazarAdelantoSerializer, ResumenTrabajadorSerializer, EstadisticasPagosSerializer
)
from .services import PagoService
from .repositories import PagosRepositoryManager
from .utils import generar_reporte_planilla_excel, enviar_email_boleta
from .exceptions import PagoServiceException

logger = logging.getLogger(__name__)


class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de pagos
    
    Provee endpoints para CRUD de pagos individuales
    """
    
    queryset = Pago.objects.filter(activo=True)
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]  # DjangoFilterBackend comentado temporalmente
    filterset_fields = ['estado', 'planilla__año', 'planilla__mes', 'trabajador_id']
    search_fields = ['trabajador_nombre', 'trabajador_documento', 'trabajador_id']
    ordering_fields = ['fecha_calculo', 'monto_neto', 'trabajador_nombre']
    ordering = ['-fecha_calculo']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pago_service = PagoService()
        self.repositories = PagosRepositoryManager()
    
    def get_queryset(self):
        """Personaliza el queryset con filtros adicionales"""
        queryset = super().get_queryset()
        
        # Filtro por rango de fechas
        fecha_inicio = self.request.query_params.get('fecha_inicio')
        fecha_fin = self.request.query_params.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_calculo__date__gte=fecha_inicio,
                fecha_calculo__date__lte=fecha_fin
            )
        
        # Filtro por monto mínimo/máximo
        monto_min = self.request.query_params.get('monto_min')
        monto_max = self.request.query_params.get('monto_max')
        
        if monto_min:
            queryset = queryset.filter(monto_neto__gte=monto_min)
        if monto_max:
            queryset = queryset.filter(monto_neto__lte=monto_max)
        
        # Incluir relaciones para optimizar consultas
        return queryset.select_related('planilla').prefetch_related(
            'pagodescuento_set__descuento',
            'pagobonificacion_set__bonificacion'
        )
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba un pago individual"""
        try:
            pago = self.get_object()
            
            if pago.estado != 'CALCULADO':
                return Response(
                    {'error': 'El pago no está en estado para ser aprobado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pago.aprobar(request.user)
            
            serializer = self.get_serializer(pago)
            return Response({
                'message': 'Pago aprobado exitosamente',
                'pago': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error aprobando pago {pk}: {str(e)}")
            return Response(
                {'error': f'Error al aprobar pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def marcar_pagado(self, request, pk=None):
        """Marca un pago como pagado"""
        try:
            pago = self.get_object()
            
            if pago.estado != 'APROBADO':
                return Response(
                    {'error': 'El pago debe estar aprobado para marcarlo como pagado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pago.marcar_como_pagado()
            
            serializer = self.get_serializer(pago)
            return Response({
                'message': 'Pago marcado como pagado',
                'pago': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error marcando pago como pagado {pk}: {str(e)}")
            return Response(
                {'error': f'Error al marcar pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        """Anula un pago"""
        try:
            pago = self.get_object()
            
            if pago.estado == 'ANULADO':
                return Response(
                    {'error': 'El pago ya está anulado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pago.anular()
            
            serializer = self.get_serializer(pago)
            return Response({
                'message': 'Pago anulado exitosamente',
                'pago': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error anulando pago {pk}: {str(e)}")
            return Response(
                {'error': f'Error al anular pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtiene estadísticas de pagos"""
        try:
            año = request.query_params.get('año')
            mes = request.query_params.get('mes')
            
            if not año or not mes:
                return Response(
                    {'error': 'Parámetros año y mes son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            estadisticas = self.repositories.pagos.obtener_estadisticas_mensuales(
                int(año), int(mes)
            )
            
            serializer = EstadisticasPagosSerializer({
                'periodo': f"{año}-{mes:0>2}",
                **estadisticas
            })
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return Response(
                {'error': f'Error al obtener estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def por_trabajador(self, request):
        """Obtiene pagos de un trabajador específico"""
        trabajador_id = request.query_params.get('trabajador_id')
        
        if not trabajador_id:
            return Response(
                {'error': 'Parámetro trabajador_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagos = self.repositories.pagos.buscar_por_trabajador(trabajador_id)
        
        # Aplicar paginación
        page = self.paginate_queryset(pagos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pagos, many=True)
        return Response(serializer.data)


class PlanillaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de planillas
    
    Provee endpoints para CRUD de planillas y acciones especiales
    """
    
    queryset = Planilla.objects.filter(activo=True)
    serializer_class = PlanillaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]  # DjangoFilterBackend comentado temporalmente
    filterset_fields = ['año', 'mes', 'procesada', 'aprobada']
    search_fields = ['nombre']
    ordering_fields = ['año', 'mes', 'fecha_procesamiento']
    ordering = ['-año', '-mes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pago_service = PagoService()
        self.repositories = PagosRepositoryManager()
    
    @action(detail=False, methods=['post'])
    def generar_planilla(self, request):
        """Genera una planilla completa para un periodo"""
        try:
            serializer = GenerarPlanillaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            planilla = self.pago_service.generar_planilla(
                año=serializer.validated_data['año'],
                mes=serializer.validated_data['mes'],
                trabajadores_data=serializer.validated_data['trabajadores'],
                usuario=request.user
            )
            
            planilla_serializer = PlanillaSerializer(planilla)
            return Response({
                'message': 'Planilla generada exitosamente',
                'planilla': planilla_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except PagoServiceException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generando planilla: {str(e)}")
            return Response(
                {'error': f'Error interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba una planilla procesada"""
        try:
            serializer = AprobarPlanillaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            planilla = self.get_object()
            
            if not planilla.puede_aprobar():
                return Response(
                    {'error': 'La planilla no puede ser aprobada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success = self.pago_service.aprobar_planilla(
                str(planilla.id), 
                request.user
            )
            
            if success:
                planilla.refresh_from_db()
                planilla_serializer = self.get_serializer(planilla)
                return Response({
                    'message': 'Planilla aprobada exitosamente',
                    'planilla': planilla_serializer.data
                })
            
            return Response(
                {'error': 'No se pudo aprobar la planilla'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Error aprobando planilla {pk}: {str(e)}")
            return Response(
                {'error': f'Error al aprobar planilla: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def pagos(self, request, pk=None):
        """Obtiene todos los pagos de una planilla"""
        planilla = self.get_object()
        pagos = self.repositories.pagos.buscar_por_planilla(str(planilla.id))
        
        # Aplicar paginación
        page = self.paginate_queryset(pagos)
        if page is not None:
            serializer = PagoSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PagoSerializer(pagos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def exportar_excel(self, request, pk=None):
        """Exporta la planilla a Excel"""
        try:
            planilla = self.get_object()
            
            # Generar archivo Excel
            excel_buffer = generar_reporte_planilla_excel(planilla)
            
            # Preparar respuesta HTTP
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            filename = f"planilla_{planilla.año}_{planilla.mes:02d}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error exportando planilla {pk}: {str(e)}")
            return Response(
                {'error': f'Error al exportar planilla: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas_anuales(self, request):
        """Obtiene estadísticas anuales de planillas"""
        try:
            año = request.query_params.get('año')
            
            if not año:
                return Response(
                    {'error': 'Parámetro año es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            estadisticas = self.repositories.planillas.obtener_estadisticas_anuales(int(año))
            
            return Response({
                'año': int(año),
                **estadisticas
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas anuales: {str(e)}")
            return Response(
                {'error': f'Error al obtener estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BoletaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de boletas de pago
    
    Provee endpoints para CRUD de boletas individuales
    """
    
    queryset = Boleta.objects.filter(activo=True)
    serializer_class = BoletaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_fields = ['pago__estado', 'pago__trabajador_id']
    search_fields = ['pago__trabajador_nombre', 'pago__trabajador_documento']
    ordering_fields = ['fecha_generacion']
    ordering = ['-fecha_generacion']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pago_service = PagoService()
        self.repositories = PagosRepositoryManager()
    
    def get_queryset(self):
        """Personaliza el queryset con relaciones optimizadas"""
        return super().get_queryset().select_related(
            'pago', 'pago__planilla'
        )
    
    @action(detail=False, methods=['post'])
    def generar_boleta(self, request):
        """Genera una boleta de pago individual"""
        try:
            serializer = GenerarBoletaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            pago_id = serializer.validated_data['pago_id']
            incluir_datos_empresa = serializer.validated_data.get('incluir_datos_empresa', True)
            
            boleta = self.pago_service.generar_boleta(
                pago_id=pago_id,
                incluir_datos_empresa=incluir_datos_empresa
            )
            
            boleta_serializer = BoletaSerializer(boleta)
            return Response({
                'message': 'Boleta generada exitosamente',
                'boleta': boleta_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except PagoServiceException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generando boleta: {str(e)}")
            return Response(
                {'error': f'Error interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def descargar_pdf(self, request, pk=None):
        """Descarga el PDF de la boleta"""
        try:
            boleta = self.get_object()
            
            if not boleta.archivo_pdf:
                return Response(
                    {'error': 'La boleta no tiene archivo PDF asociado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Servir archivo PDF
            response = HttpResponse(
                boleta.archivo_pdf,
                content_type='application/pdf'
            )
            
            filename = f"boleta_{boleta.pago.trabajador_documento}_{boleta.fecha_generacion.strftime('%Y%m')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error descargando PDF boleta {pk}: {str(e)}")
            return Response(
                {'error': f'Error al descargar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def enviar_email(self, request, pk=None):
        """Envía la boleta por email al trabajador"""
        try:
            boleta = self.get_object()
            email_trabajador = request.data.get('email')
            
            if not email_trabajador:
                return Response(
                    {'error': 'Email del trabajador es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Enviar email con boleta
            success = enviar_email_boleta(boleta, email_trabajador)
            
            if success:
                return Response({
                    'message': f'Boleta enviada exitosamente a {email_trabajador}'
                })
            
            return Response(
                {'error': 'No se pudo enviar el email'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        except Exception as e:
            logger.error(f"Error enviando email boleta {pk}: {str(e)}")
            return Response(
                {'error': f'Error al enviar email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdelantoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de adelantos
    
    Provee endpoints para CRUD de adelantos y flujo de aprobación
    """
    
    queryset = Adelanto.objects.filter(activo=True)
    serializer_class = AdelantoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'trabajador_id']
    search_fields = ['trabajador_nombre', 'trabajador_documento', 'motivo']
    ordering_fields = ['fecha_solicitud', 'fecha_limite_pago', 'monto']
    ordering = ['-fecha_solicitud']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pago_service = PagoService()
        self.repositories = PagosRepositoryManager()
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba un adelanto pendiente"""
        try:
            serializer = AprobarAdelantoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            adelanto = self.get_object()
            
            if adelanto.estado != 'PENDIENTE':
                return Response(
                    {'error': 'El adelanto no está en estado pendiente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success = self.pago_service.procesar_adelanto(
                str(adelanto.id),
                'APROBADO',
                request.user,
                observaciones=serializer.validated_data.get('observaciones')
            )
            
            if success:
                adelanto.refresh_from_db()
                adelanto_serializer = self.get_serializer(adelanto)
                return Response({
                    'message': 'Adelanto aprobado exitosamente',
                    'adelanto': adelanto_serializer.data
                })
            
            return Response(
                {'error': 'No se pudo aprobar el adelanto'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Error aprobando adelanto {pk}: {str(e)}")
            return Response(
                {'error': f'Error al aprobar adelanto: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DescuentoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de descuentos"""
    
    queryset = Descuento.objects.filter(activo=True)
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_fields = ['tipo', 'obligatorio']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'porcentaje', 'monto_fijo']
    ordering = ['nombre']


class BonificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de bonificaciones"""
    
    queryset = Bonificacion.objects.filter(activo=True)
    serializer_class = BonificacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_fields = ['tipo', 'imponible']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'porcentaje', 'monto_fijo']
    ordering = ['nombre']
