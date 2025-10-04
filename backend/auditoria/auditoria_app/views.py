"""
Vistas para el microservicio de auditoría
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .models import ActividadSistema
from .serializers import ActividadSistemaSerializer, ActividadSistemaCreateSerializer
from .services import AuditoriaService
from .repositories import AuditoriaRepository
from .middleware.observer import webhook_handler, observer

logger = logging.getLogger('audit.views')


class ActividadSistemaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar actividades del sistema
    Solo lectura - no se permiten modificaciones directas
    """
    queryset = ActividadSistema.objects.all()
    serializer_class = ActividadSistemaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = {
        'usuario_id': ['exact'],
        'accion': ['exact', 'in'],
        'recurso': ['exact', 'in'],
        'microservicio': ['exact', 'in'],
        'exito': ['exact'],
        'fecha_hora': ['gte', 'lte', 'date'],
        'criticidad': ['exact', 'in']
    }
    search_fields = ['detalle', 'usuario_email', 'ip_address']
    ordering_fields = ['fecha_hora', 'criticidad', 'duracion_ms']
    ordering = ['-fecha_hora']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auditoria_service = AuditoriaService()
        self.auditoria_repository = AuditoriaRepository()
    
    def get_queryset(self):
        """
        Filtrar queryset basado en permisos del usuario
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Solo admins pueden ver todas las actividades
        if not user.is_staff:
            # Usuarios normales solo ven sus propias actividades
            queryset = queryset.filter(usuario_id=user.id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de auditoría
        GET /api/logs/estadisticas/
        """
        try:
            # Parámetros de filtro
            dias = int(request.GET.get('dias', 7))
            usuario_id = request.GET.get('usuario_id')
            microservicio = request.GET.get('microservicio')
            
            # Obtener estadísticas
            stats = self.auditoria_service.obtener_estadisticas(
                dias=dias,
                usuario_id=usuario_id,
                microservicio=microservicio
            )
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return Response(
                {'error': 'Error al obtener estadísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def actividad_sospechosa(self, request):
        """
        Obtener actividades sospechosas
        GET /api/logs/actividad_sospechosa/
        """
        try:
            actividades = self.auditoria_service.detectar_actividad_sospechosa()
            serializer = self.get_serializer(actividades, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error al obtener actividad sospechosa: {str(e)}")
            return Response(
                {'error': 'Error al obtener actividad sospechosa'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """
        Exportar logs a CSV
        GET /api/logs/exportar_csv/
        """
        try:
            # Obtener filtros
            filtros = self._get_export_filters(request)
            
            # Generar CSV
            csv_data = self.auditoria_service.exportar_csv(filtros)
            
            # Crear response
            response = HttpResponse(csv_data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error al exportar CSV: {str(e)}")
            return Response(
                {'error': 'Error al exportar CSV'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def exportar_excel(self, request):
        """
        Exportar logs a Excel
        GET /api/logs/exportar_excel/
        """
        try:
            # Obtener filtros
            filtros = self._get_export_filters(request)
            
            # Generar Excel
            excel_data = self.auditoria_service.exportar_excel(filtros)
            
            # Crear response
            response = HttpResponse(
                excel_data, 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error al exportar Excel: {str(e)}")
            return Response(
                {'error': 'Error al exportar Excel'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def exportar_pdf(self, request):
        """
        Exportar logs a PDF
        GET /api/logs/exportar_pdf/
        """
        try:
            # Obtener filtros
            filtros = self._get_export_filters(request)
            
            # Generar PDF
            pdf_data = self.auditoria_service.exportar_pdf(filtros)
            
            # Crear response
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error al exportar PDF: {str(e)}")
            return Response(
                {'error': 'Error al exportar PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def metricas_rendimiento(self, request):
        """
        Obtener métricas de rendimiento del sistema
        GET /api/logs/metricas_rendimiento/
        """
        try:
            metricas = self.auditoria_service.obtener_metricas_rendimiento()
            return Response(metricas)
            
        except Exception as e:
            logger.error(f"Error al obtener métricas de rendimiento: {str(e)}")
            return Response(
                {'error': 'Error al obtener métricas de rendimiento'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def limpiar_logs_antiguos(self, request):
        """
        Limpiar logs antiguos
        POST /api/logs/limpiar_logs_antiguos/
        """
        try:
            dias = int(request.data.get('dias', 90))
            resultado = self.auditoria_service.limpiar_logs_antiguos(dias)
            return Response(resultado)
            
        except Exception as e:
            logger.error(f"Error al limpiar logs antiguos: {str(e)}")
            return Response(
                {'error': 'Error al limpiar logs antiguos'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_export_filters(self, request) -> Dict[str, Any]:
        """
        Obtener filtros para exportación
        """
        filtros = {}
        
        # Filtros de fecha
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        if fecha_inicio:
            filtros['fecha_inicio'] = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
        if fecha_fin:
            filtros['fecha_fin'] = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
        
        # Otros filtros
        if request.GET.get('usuario_id'):
            filtros['usuario_id'] = int(request.GET.get('usuario_id'))
        if request.GET.get('accion'):
            filtros['accion'] = request.GET.get('accion')
        if request.GET.get('recurso'):
            filtros['recurso'] = request.GET.get('recurso')
        if request.GET.get('microservicio'):
            filtros['microservicio'] = request.GET.get('microservicio')
        if request.GET.get('exito'):
            filtros['exito'] = request.GET.get('exito').lower() == 'true'
        
        return filtros


@method_decorator(csrf_exempt, name='dispatch')
class WebhookDocumentView(View):
    """
    Webhook para recibir notificaciones de cambios en documentos
    """
    
    def post(self, request):
        """
        Procesar webhook de documentos
        POST /api/webhooks/documents/
        """
        try:
            data = json.loads(request.body)
            success = webhook_handler.handle_document_webhook(data)
            
            if success:
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error en webhook de documentos: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Internal error'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookPaymentView(View):
    """
    Webhook para recibir notificaciones de cambios en pagos
    """
    
    def post(self, request):
        """
        Procesar webhook de pagos
        POST /api/webhooks/payments/
        """
        try:
            data = json.loads(request.body)
            success = webhook_handler.handle_payment_webhook(data)
            
            if success:
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error en webhook de pagos: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Internal error'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookUserView(View):
    """
    Webhook para recibir notificaciones de cambios en usuarios
    """
    
    def post(self, request):
        """
        Procesar webhook de usuarios
        POST /api/webhooks/users/
        """
        try:
            data = json.loads(request.body)
            success = webhook_handler.handle_user_webhook(data)
            
            if success:
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error en webhook de usuarios: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Internal error'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookAttendanceView(View):
    """
    Webhook para recibir notificaciones de cambios en asistencias
    """
    
    def post(self, request):
        """
        Procesar webhook de asistencias
        POST /api/webhooks/attendance/
        """
        try:
            data = json.loads(request.body)
            success = webhook_handler.handle_attendance_webhook(data)
            
            if success:
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error en webhook de asistencias: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Internal error'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookGenericView(View):
    """
    Webhook para recibir notificaciones genéricas
    """
    
    def post(self, request):
        """
        Procesar webhook genérico
        POST /api/webhooks/generic/
        """
        try:
            data = json.loads(request.body)
            success = webhook_handler.handle_generic_webhook(data)
            
            if success:
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error en webhook genérico: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Internal error'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Health check endpoint
    GET /api/health/
    """
    try:
        # Verificar conexión a la base de datos
        count = ActividadSistema.objects.count()
        
        return Response({
            'status': 'healthy',
            'microservice': 'auditoria',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'total_logs': count
        })
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'microservice': 'auditoria',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_info(request):
    """
    Información del sistema
    GET /api/system-info/
    """
    try:
        auditoria_service = AuditoriaService()
        
        # Obtener estadísticas del sistema
        total_logs = ActividadSistema.objects.count()
        logs_hoy = ActividadSistema.objects.filter(
            fecha__date=datetime.now().date()
        ).count()
        
        # Últimas 24 horas
        hace_24h = datetime.now() - timedelta(hours=24)
        logs_24h = ActividadSistema.objects.filter(
            fecha__gte=hace_24h
        ).count()
        
        # Usuarios únicos en las últimas 24 horas
        usuarios_activos = ActividadSistema.objects.filter(
            fecha__gte=hace_24h,
            usuario_id__isnull=False
        ).values('usuario_id').distinct().count()
        
        return Response({
            'microservice': 'auditoria',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_logs': total_logs,
                'logs_today': logs_hoy,
                'logs_24h': logs_24h,
                'active_users_24h': usuarios_activos
            },
            'database': {
                'status': 'connected',
                'type': 'MySQL'
            }
        })
        
    except Exception as e:
        logger.error(f"Error al obtener información del sistema: {str(e)}")
        return Response({
            'error': 'Error al obtener información del sistema'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== VISTAS DE WEBHOOK ==========

class WebhookDocumentView(View):
    """
    Webhook para recibir notificaciones de cambios en documentos
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            observer.notify_document_change(
                action=data.get('action', 'UPDATE'),
                document_id=data.get('document_id'),
                user_id=data.get('user_id'),
                details=data.get('details', {})
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error en webhook documentos: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)


class WebhookPaymentView(View):
    """
    Webhook para recibir notificaciones de cambios en pagos
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            observer.notify_payment_change(
                action=data.get('action', 'UPDATE'),
                payment_id=data.get('payment_id'),
                user_id=data.get('user_id'),
                details=data.get('details', {})
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error en webhook pagos: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)


class WebhookUserView(View):
    """
    Webhook para recibir notificaciones de cambios en usuarios
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            observer.notify_user_change(
                action=data.get('action', 'UPDATE'),
                user_id=data.get('user_id'),
                details=data.get('details', {})
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error en webhook usuarios: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)


class WebhookAttendanceView(View):
    """
    Webhook para recibir notificaciones de cambios en asistencia
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            observer.notify_attendance_change(
                action=data.get('action', 'UPDATE'),
                attendance_id=data.get('attendance_id'),
                user_id=data.get('user_id'),
                details=data.get('details', {})
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error en webhook asistencia: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)


class WebhookGenericView(View):
    """
    Webhook genérico para cualquier tipo de notificación
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            auditoria_service = AuditoriaService()
            auditoria_service.registrar_actividad(
                usuario_id=data.get('user_id'),
                accion=data.get('action', 'OTHER'),
                recurso=data.get('resource', 'OTHER'),
                detalle=data.get('details', {}),
                **data.get('extra_data', {})
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error en webhook genérico: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
