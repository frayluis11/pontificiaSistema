"""
Tareas asíncronas simplificadas para el microservicio de reportes
"""

from celery import shared_task
from django.utils import timezone
from django.db import models
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def procesar_reporte_async(self, reporte_id: str) -> Dict[str, Any]:
    """
    Procesa un reporte de forma asíncrona (versión simplificada)
    """
    try:
        # Import aquí para evitar problemas de circular imports
        from .models import Reporte
        from .services import ReporteService
        
        # Obtener el reporte
        reporte = Reporte.objects.get(id=reporte_id)
        reporte_service = ReporteService()
        
        # Actualizar estado a procesando
        reporte.estado = 'PROCESANDO'
        reporte.fecha_inicio_procesamiento = timezone.now()
        reporte.save()
        
        # Procesar según el tipo de reporte
        resultado = None
        if reporte.tipo == 'ASISTENCIA':
            resultado = {'mensaje': 'Reporte de asistencia procesado'}
        elif reporte.tipo == 'PAGOS':
            resultado = {'mensaje': 'Reporte de pagos procesado'}
        elif reporte.tipo == 'METRICAS':
            resultado = {'mensaje': 'Reporte de métricas procesado'}
        else:
            resultado = {'mensaje': 'Reporte personalizado procesado'}
        
        # Actualizar estado a completado
        reporte.estado = 'COMPLETADO'
        reporte.fecha_fin_procesamiento = timezone.now()
        reporte.save()
        
        return {
            'status': 'SUCCESS',
            'reporte_id': str(reporte.id),
            'resultado': resultado
        }
        
    except Exception as e:
        logger.error(f"Error procesando reporte {reporte_id}: {str(e)}")
        
        # Actualizar estado a error si el reporte existe
        try:
            from .models import Reporte
            reporte = Reporte.objects.get(id=reporte_id)
            reporte.estado = 'ERROR'
            reporte.save()
        except:
            pass
            
        return {
            'status': 'ERROR',
            'error': str(e)
        }

@shared_task
def limpiar_reportes_expirados():
    """
    Limpia reportes expirados (versión simplificada)
    """
    try:
        from .models import Reporte
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=30)
        reportes_expirados = Reporte.objects.filter(
            fecha_creacion__lt=fecha_limite,
            estado='COMPLETADO'
        )
        
        count = reportes_expirados.count()
        reportes_expirados.delete()
        
        return f"Eliminados {count} reportes expirados"
        
    except Exception as e:
        logger.error(f"Error limpiando reportes: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def generar_estadisticas_reportes():
    """
    Genera estadísticas básicas de reportes (versión simplificada)
    """
    try:
        from .models import Reporte
        
        total_reportes = Reporte.objects.count()
        reportes_por_tipo = Reporte.objects.values('tipo').annotate(
            count=models.Count('tipo')
        )
        reportes_por_usuario = Reporte.objects.values('autor_id').annotate(
            count=models.Count('autor_id')
        )
        
        return {
            'total_reportes': total_reportes,
            'por_tipo': list(reportes_por_tipo),
            'por_usuario': list(reportes_por_usuario),
            'fecha_actualizacion': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generando estadísticas: {str(e)}")
        return {'error': str(e)}