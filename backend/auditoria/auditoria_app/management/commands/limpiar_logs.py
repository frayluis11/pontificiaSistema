"""
Comando para limpiar logs antiguos de auditoría
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count

from auditoria_app.models import ActividadSistema


class Command(BaseCommand):
    help = 'Limpia logs de auditoría antiguos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=90,
            help='Días de antigüedad para eliminar logs (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo simulación sin eliminar datos'
        )
        parser.add_argument(
            '--keep-critical',
            action='store_true',
            help='Mantener logs críticos independientemente de la antigüedad'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Tamaño del lote para eliminación (default: 1000)'
        )
    
    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']
        keep_critical = options['keep_critical']
        batch_size = options['batch_size']
        
        # Calcular fecha límite
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        self.stdout.write(self.style.SUCCESS(
            f'Limpiando logs anteriores a {fecha_limite.strftime("%Y-%m-%d %H:%M:%S")}'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO SIMULACIÓN - No se eliminarán datos'))
        
        # Construir query base
        query = ActividadSistema.objects.filter(fecha_hora__lt=fecha_limite)
        
        # Excluir logs críticos si se solicita
        if keep_critical:
            query = query.exclude(criticidad='CRITICAL')
            self.stdout.write('Manteniendo logs críticos')
        
        # Obtener estadísticas antes de eliminar
        total_logs = ActividadSistema.objects.count()
        logs_a_eliminar = query.count()
        
        self.stdout.write(f'Total de logs en el sistema: {total_logs}')
        self.stdout.write(f'Logs a eliminar: {logs_a_eliminar}')
        
        if logs_a_eliminar == 0:
            self.stdout.write('No hay logs para eliminar')
            return
        
        # Mostrar desglose por microservicio
        self.stdout.write('\n--- Desglose por microservicio ---')
        stats_microservicio = query.values('microservicio').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for stat in stats_microservicio:
            microservicio = stat['microservicio'] or 'SIN_MICROSERVICIO'
            count = stat['count']
            self.stdout.write(f'{microservicio}: {count} logs')
        
        # Mostrar desglose por criticidad
        self.stdout.write('\n--- Desglose por criticidad ---')
        stats_criticidad = query.values('criticidad').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for stat in stats_criticidad:
            criticidad = stat['criticidad'] or 'SIN_CRITICIDAD'
            count = stat['count']
            self.stdout.write(f'{criticidad}: {count} logs')
        
        # Confirmar eliminación
        if not dry_run:
            confirm = input(f'\n¿Confirma la eliminación de {logs_a_eliminar} logs? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operación cancelada')
                return
        
        # Proceder con eliminación
        if not dry_run:
            self.stdout.write('Iniciando eliminación...')
            
            eliminados_total = 0
            
            # Eliminar en lotes para evitar problemas de memoria
            while True:
                # Obtener IDs de un lote
                ids_lote = list(query.values_list('id', flat=True)[:batch_size])
                
                if not ids_lote:
                    break
                
                # Eliminar el lote
                eliminados_lote = ActividadSistema.objects.filter(
                    id__in=ids_lote
                ).delete()[0]
                
                eliminados_total += eliminados_lote
                
                self.stdout.write(f'Eliminados: {eliminados_total}/{logs_a_eliminar}')
            
            # Estadísticas finales
            logs_restantes = ActividadSistema.objects.count()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n¡Limpieza completada!'
            ))
            self.stdout.write(f'Logs eliminados: {eliminados_total}')
            self.stdout.write(f'Logs restantes: {logs_restantes}')
            self.stdout.write(f'Espacio liberado: ~{eliminados_total * 0.001:.2f} MB (estimado)')
            
        else:
            self.stdout.write(self.style.WARNING(
                f'SIMULACIÓN: Se eliminarían {logs_a_eliminar} logs'
            ))
        
        # Recomendaciones
        self.stdout.write('\n--- Recomendaciones ---')
        
        if logs_a_eliminar > total_logs * 0.8:
            self.stdout.write(self.style.WARNING(
                'Se eliminaría más del 80% de los logs. '
                'Considere reducir el período de retención.'
            ))
        
        if keep_critical:
            logs_criticos = ActividadSistema.objects.filter(
                fecha_hora__lt=fecha_limite,
                criticidad='CRITICAL'
            ).count()
            if logs_criticos > 0:
                self.stdout.write(f'Se mantuvieron {logs_criticos} logs críticos antiguos')
        
        # Sugerir próxima limpieza
        proxima_limpieza = timezone.now() + timedelta(days=30)
        self.stdout.write(f'Próxima limpieza recomendada: {proxima_limpieza.strftime("%Y-%m-%d")}')