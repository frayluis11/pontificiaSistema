"""
Configuración de Celery para el microservicio de reportes

Celery se usa para tareas largas como generación de reportes complejos,
procesamiento de datos y exportación de archivos grandes.
"""

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Establecer el módulo de configuración de Django para el programa 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reportes_service.settings')

app = Celery('reportes_service')

# Usar una string aquí significa que el worker no tiene que serializar
# el objeto de configuración hacia child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar módulos de tareas de todas las aplicaciones Django registradas
app.autodiscover_tasks()

# Configuración adicional para el microservicio de reportes
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    
    # Configuración específica para reportes
    task_routes={
        'reportes_app.tasks.generar_reporte_async': {'queue': 'reportes'},
        'reportes_app.tasks.exportar_metricas_async': {'queue': 'exportacion'},
        'reportes_app.tasks.procesar_datos_async': {'queue': 'procesamiento'},
    },
    
    # Límites de tiempo para tareas largas
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    
    # Configuración de reintentos
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Beat schedule para tareas periódicas
    beat_schedule={
        'generar-metricas-diarias': {
            'task': 'reportes_app.tasks.generar_metricas_diarias',
            'schedule': 86400.0,  # Cada 24 horas
        },
        'limpiar-reportes-antiguos': {
            'task': 'reportes_app.tasks.limpiar_reportes_antiguos',
            'schedule': 604800.0,  # Cada semana
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    """Tarea de debug para verificar que Celery funciona"""
    print(f'Request: {self.request!r}')