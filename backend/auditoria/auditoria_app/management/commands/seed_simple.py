"""
Comando simple para generar datos de prueba de auditoría
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
import uuid

from auditoria_app.models import ActividadSistema


class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema de auditoría'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=50,
            help='Cantidad de registros de auditoría a generar (default: 50)'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpiar datos existentes antes de generar nuevos'
        )
    
    def handle(self, *args, **options):
        cantidad = options['cantidad']
        limpiar = options['limpiar']
        
        self.stdout.write(self.style.SUCCESS(
            f'Generando {cantidad} registros de auditoría...'
        ))
        
        if limpiar:
            self.stdout.write('Limpiando datos existentes...')
            ActividadSistema.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos existentes eliminados'))
        
        # Datos de ejemplo
        usuarios_ejemplo = [
            {'id': 1, 'email': 'admin@pontificia.edu'},
            {'id': 2, 'email': 'secretaria@pontificia.edu'},
            {'id': 3, 'email': 'estudiante1@pontificia.edu'},
            {'id': 4, 'email': 'profesor@pontificia.edu'},
        ]
        
        registros_creados = 0
        
        for i in range(cantidad):
            try:
                usuario = random.choice(usuarios_ejemplo)
                accion = random.choice(['CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT'])
                recurso = random.choice(['USERS', 'DOCUMENTS', 'PAYMENTS', 'ATTENDANCE'])
                
                # Fecha aleatoria en los últimos 7 días
                fecha_random = timezone.now() - timedelta(
                    days=random.randint(0, 7),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                detalle = {
                    'accion_realizada': accion,
                    'timestamp': fecha_random.isoformat(),
                    'generado_por_seed': True
                }
                
                actividad = ActividadSistema.objects.create(
                    usuario_id=usuario['id'],
                    usuario_email=usuario['email'],
                    accion=accion,
                    recurso=recurso,
                    recurso_id=str(uuid.uuid4())[:8],
                    fecha=fecha_random,
                    detalle=detalle,
                    ip_address=f"192.168.1.{random.randint(100, 200)}",
                    user_agent="Mozilla/5.0 (Test Browser)",
                    session_key=f"session_{random.randint(1000, 9999)}",
                    metodo_http=random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                    url_solicitada=f"/api/{recurso.lower()}/",
                    codigo_estado=random.choice([200, 201, 400, 404, 500]),
                    nivel_criticidad=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                    duracion_ms=random.randint(50, 2000)
                )
                
                registros_creados += 1
                
                if registros_creados % 10 == 0:
                    self.stdout.write(f'Creados {registros_creados} registros...')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creando registro {i}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'¡Éxito! Se crearon {registros_creados} registros de auditoría'
        ))
        
        # Mostrar estadísticas
        total_registros = ActividadSistema.objects.count()
        self.stdout.write(f'Total de registros en la base de datos: {total_registros}')