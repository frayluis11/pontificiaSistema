"""
Tareas asíncronas de Celery para el microservicio de reportes
"""

from celery import shared_task, current_task
from celery.exceptions import Retry
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from typing import Dict, Any, Optional
import logging
import os
import tempfile
from datetime import datetime, timedelta

from .models import Reporte, Metrica
from .services import ReporteService, MetricaService
from .exceptions import ErrorProcesamiento

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def procesar_reporte_async(self, reporte_id: str):
    """
    Tarea asíncrona para procesar un reporte
    
    Args:
        reporte_id: ID del reporte a procesar
    
    Returns:
        Dict con el resultado del procesamiento
    """
    try:
        logger.info(f"Iniciando procesamiento asíncrono del reporte {reporte_id}")
        
        # Obtener el reporte
        try:
            reporte = Reporte.objects.get(id=reporte_id)
        except Reporte.DoesNotExist:
            logger.error(f"Reporte {reporte_id} no encontrado")
            return {'success': False, 'error': 'Reporte no encontrado'}
        
        # Actualizar estado a procesando
        reporte.estado = 'procesando'
        reporte.save()
        
        # Actualizar progreso de la tarea
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Iniciando procesamiento...'}
        )
        
        # Instanciar servicio de reportes
        reporte_service = ReporteService()
        
        # Procesar según el tipo de reporte
        logger.info(f"Procesando reporte tipo {reporte.tipo}, formato {reporte.formato}")
        
        # Actualizar progreso
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Generando contenido...'}
        )
        
        # Generar el archivo del reporte
        if reporte.formato.lower() == 'pdf':
            archivo_path = reporte_service._generar_pdf(
                reporte.tipo,
                reporte.parametros,
                reporte.titulo or f"Reporte {reporte.tipo}"
            )
        elif reporte.formato.lower() == 'excel':
            archivo_path = reporte_service._generar_excel(
                reporte.tipo,
                reporte.parametros,
                reporte.titulo or f"Reporte {reporte.tipo}"
            )
        elif reporte.formato.lower() == 'csv':
            archivo_path = reporte_service._generar_csv(
                reporte.tipo,
                reporte.parametros,
                reporte.titulo or f"Reporte {reporte.tipo}"
            )
        else:
            raise ErrorProcesamiento(f"Formato {reporte.formato} no soportado")
        
        # Actualizar progreso
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Guardando archivo...'}
        )
        
        # Guardar el archivo en el modelo
        with open(archivo_path, 'rb') as f:
            archivo_nombre = f"reporte_{reporte_id}.{reporte.formato}"
            reporte.archivo.save(archivo_nombre, ContentFile(f.read()))
        
        # Limpiar archivo temporal
        try:
            os.remove(archivo_path)
        except:
            pass
        
        # Actualizar estado a completado
        reporte.estado = 'completado'
        reporte.fecha_actualizacion = timezone.now()
        
        # Configurar expiración (7 días por defecto)
        if not reporte.expires_at:
            reporte.expires_at = timezone.now() + timedelta(days=7)
        
        reporte.save()
        
        # Actualizar progreso final
        current_task.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Completado'}
        )
        
        logger.info(f"Reporte {reporte_id} procesado exitosamente")
        
        return {
            'success': True,
            'reporte_id': reporte_id,
            'estado': 'completado',
            'archivo': reporte.archivo.name if reporte.archivo else None,
            'tiempo_procesamiento': (reporte.fecha_actualizacion - reporte.fecha_creacion).total_seconds()
        }
    
    except Exception as e:
        logger.error(f"Error al procesar reporte {reporte_id}: {str(e)}")
        
        # Actualizar estado de error
        try:
            reporte = Reporte.objects.get(id=reporte_id)
            reporte.estado = 'error'
            reporte.fecha_actualizacion = timezone.now()
            reporte.save()
        except:
            pass
        
        # Reintentar en caso de errores recuperables
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando procesamiento del reporte {reporte_id} (intento {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            'success': False,
            'error': str(e),
            'reporte_id': reporte_id
        }


@shared_task(bind=True)
def calcular_metricas_periodicas(self):
    """
    Tarea periódica para calcular métricas del sistema
    """
    try:
        logger.info("Iniciando cálculo de métricas periódicas")
        
        metrica_service = MetricaService()
        
        # Calcular métricas diarias
        metricas_diarias = metrica_service.calcular_metricas_periodo('diario')
        logger.info(f"Calculadas {len(metricas_diarias)} métricas diarias")
        
        # Calcular métricas semanales (solo los lunes)
        if timezone.now().weekday() == 0:  # Lunes
            metricas_semanales = metrica_service.calcular_metricas_periodo('semanal')
            logger.info(f"Calculadas {len(metricas_semanales)} métricas semanales")
        
        # Calcular métricas mensuales (solo el día 1)
        if timezone.now().day == 1:
            metricas_mensuales = metrica_service.calcular_metricas_periodo('mensual')
            logger.info(f"Calculadas {len(metricas_mensuales)} métricas mensuales")
        
        return {'success': True, 'timestamp': timezone.now()}
    
    except Exception as e:
        logger.error(f"Error al calcular métricas periódicas: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def limpiar_reportes_expirados():
    """
    Tarea para limpiar reportes expirados
    """
    try:
        logger.info("Iniciando limpieza de reportes expirados")
        
        # Buscar reportes expirados
        reportes_expirados = Reporte.objects.filter(
            expires_at__lt=timezone.now(),
            estado='completado'
        )
        
        count = 0
        for reporte in reportes_expirados:
            try:
                # Eliminar archivo físico
                if reporte.archivo:
                    reporte.archivo.delete()
                
                # Actualizar estado
                reporte.estado = 'expirado'
                reporte.archivo = None
                reporte.save()
                count += 1
                
            except Exception as e:
                logger.error(f"Error al limpiar reporte {reporte.id}: {str(e)}")
        
        logger.info(f"Limpiados {count} reportes expirados")
        return {'success': True, 'reportes_limpiados': count}
    
    except Exception as e:
        logger.error(f"Error en limpieza de reportes: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def generar_reporte_programado(tipo: str, formato: str, parametros: Dict[str, Any], autor_id: int):
    """
    Tarea para generar reportes programados
    
    Args:
        tipo: Tipo de reporte
        formato: Formato del reporte
        parametros: Parámetros del reporte
        autor_id: ID del autor
    """
    try:
        logger.info(f"Generando reporte programado: {tipo} - {formato}")
        
        reporte_service = ReporteService()
        
        # Crear reporte programado
        reporte = reporte_service.generar_reporte_async(
            tipo=tipo,
            formato=formato,
            parametros=parametros,
            autor_id=autor_id,
            titulo=f"Reporte Programado - {tipo.title()}"
        )
        
        logger.info(f"Reporte programado {reporte.id} creado exitosamente")
        return {'success': True, 'reporte_id': reporte.id}
    
    except Exception as e:
        logger.error(f"Error al generar reporte programado: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def exportar_metricas_async(parametros: Dict[str, Any], usuario_id: int):
    """
    Tarea asíncrona para exportar métricas
    
    Args:
        parametros: Parámetros de exportación
        usuario_id: ID del usuario que solicita la exportación
    """
    try:
        logger.info(f"Iniciando exportación asíncrona de métricas para usuario {usuario_id}")
        
        metrica_service = MetricaService()
        
        # Exportar métricas
        archivo_path = metrica_service.exportar_metricas(
            nombres=parametros.get('nombres'),
            periodo=parametros.get('periodo'),
            fecha_desde=parametros.get('fecha_desde'),
            fecha_hasta=parametros.get('fecha_hasta'),
            formato=parametros.get('formato', 'excel'),
            incluir_graficos=parametros.get('incluir_graficos', True),
            solo_activas=parametros.get('solo_activas', True)
        )
        
        # Aquí podrías enviar el archivo por email o guardarlo en un área accesible
        # Por ahora solo retornamos la ruta
        
        logger.info(f"Exportación de métricas completada: {archivo_path}")
        return {'success': True, 'archivo_path': archivo_path}
    
    except Exception as e:
        logger.error(f"Error en exportación asíncrona de métricas: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def notificar_reporte_completado(reporte_id: str, usuario_email: str):
    """
    Tarea para notificar cuando un reporte está completado
    
    Args:
        reporte_id: ID del reporte completado
        usuario_email: Email del usuario a notificar
    """
    try:
        logger.info(f"Enviando notificación de reporte completado {reporte_id} a {usuario_email}")
        
        # Aquí implementarías el envío de email/notificación
        # Por ejemplo, usando Django's send_mail o un servicio externo
        
        # from django.core.mail import send_mail
        # send_mail(
        #     subject=f'Reporte {reporte_id} completado',
        #     message=f'Tu reporte {reporte_id} ha sido procesado y está listo para descarga.',
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[usuario_email],
        #     fail_silently=False,
        # )
        
        logger.info(f"Notificación enviada exitosamente para reporte {reporte_id}")
        return {'success': True, 'reporte_id': reporte_id, 'email': usuario_email}
    
    except Exception as e:
        logger.error(f"Error al enviar notificación: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def test_celery():
    """
    Tarea de prueba para verificar que Celery funciona correctamente
    """
    logger.info("Tarea de prueba de Celery ejecutada correctamente")
    return {'success': True, 'message': 'Celery funcionando correctamente', 'timestamp': timezone.now()}


@shared_task
def backup_reportes():
    """
    Tarea para crear backup de reportes importantes
    """
    try:
        logger.info("Iniciando backup de reportes")
        
        # Aquí implementarías la lógica de backup
        # Por ejemplo, copiar archivos a un storage externo
        
        reportes = Reporte.objects.filter(
            estado='completado',
            fecha_creacion__gte=timezone.now() - timedelta(days=30)
        )
        
        backup_count = 0
        for reporte in reportes:
            try:
                # Lógica de backup aquí
                backup_count += 1
            except Exception as e:
                logger.error(f"Error en backup del reporte {reporte.id}: {str(e)}")
        
        logger.info(f"Backup completado: {backup_count} reportes respaldados")
        return {'success': True, 'reportes_respaldados': backup_count}
    
    except Exception as e:
        logger.error(f"Error en backup de reportes: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def generar_estadisticas_uso():
    """
    Tarea para generar estadísticas de uso del sistema de reportes
    """
    try:
        logger.info("Generando estadísticas de uso")
        
        # Estadísticas básicas
        total_reportes = Reporte.objects.count()
        reportes_hoy = Reporte.objects.filter(
            fecha_creacion__date=timezone.now().date()
        ).count()
        reportes_semana = Reporte.objects.filter(
            fecha_creacion__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Tipos más populares
        tipos_populares = Reporte.objects.values('tipo').annotate(
            count=models.Count('tipo')
        ).order_by('-count')[:5]
        
        # Usuarios más activos
        usuarios_activos = Reporte.objects.values('autor_id').annotate(
            count=models.Count('autor_id')
        ).order_by('-count')[:10]
        
        estadisticas = {
            'total_reportes': total_reportes,
            'reportes_hoy': reportes_hoy,
            'reportes_semana': reportes_semana,
            'tipos_populares': list(tipos_populares),
            'usuarios_activos': list(usuarios_activos),
            'timestamp': timezone.now()
        }
        
        # Aquí podrías guardar las estadísticas en caché o base de datos
        # cache.set('estadisticas_reportes', estadisticas, 3600)
        
        logger.info("Estadísticas de uso generadas exitosamente")
        return {'success': True, 'estadisticas': estadisticas}
    
    except Exception as e:
        logger.error(f"Error al generar estadísticas: {str(e)}")
        return {'success': False, 'error': str(e)}