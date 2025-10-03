"""
Comando para generar datos de prueba de auditoría
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
import uuid

from auditoria_app.models import ActividadSistema
from auditoria_app.services import AuditoriaService


class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema de auditoría'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=100,
            help='Cantidad de registros de auditoría a generar (default: 100)'
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Número de días hacia atrás para generar datos (default: 30)'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpiar datos existentes antes de generar nuevos'
        )
    
    def handle(self, *args, **options):
        cantidad = options['cantidad']
        dias = options['dias']
        limpiar = options['limpiar']
        
        self.stdout.write(self.style.SUCCESS(
            f'Generando {cantidad} registros de auditoría para los últimos {dias} días...'
        ))
        
        # Limpiar datos existentes si se solicita
        if limpiar:
            self.stdout.write('Limpiando datos existentes...')
            ActividadSistema.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos existentes eliminados'))
        
        # Generar datos de prueba
        auditoria_service = AuditoriaService()
        
        # Datos de ejemplo
        usuarios_ejemplo = [
            {'id': 1, 'email': 'admin@pontificia.edu'},
            {'id': 2, 'email': 'secretaria@pontificia.edu'},
            {'id': 3, 'email': 'estudiante1@pontificia.edu'},
            {'id': 4, 'email': 'estudiante2@pontificia.edu'},
            {'id': 5, 'email': 'profesor@pontificia.edu'},
            {'id': 6, 'email': 'contador@pontificia.edu'},
            {'id': 7, 'email': 'decano@pontificia.edu'},
            {'id': 8, 'email': 'biblioteca@pontificia.edu'},
        ]
        
        acciones_ejemplo = [
            'CREATE', 'READ', 'UPDATE', 'DELETE', 
            'LOGIN', 'LOGOUT', 'UPLOAD', 'DOWNLOAD',
            'EXPORT', 'IMPORT', 'ACCESS_DENIED', 'ERROR'
        ]
        
        recursos_ejemplo = [
            'USERS', 'USER_PROFILE', 'DOCUMENTS', 'PAYMENTS',
            'ATTENDANCE', 'REPORTS', 'AUDIT', 'AUTH', 'SYSTEM'
        ]
        
        microservicios_ejemplo = [
            'AUTH', 'USERS', 'ATTENDANCE', 'PAYMENTS', 
            'DOCUMENTS', 'REPORTS', 'AUDIT'
        ]
        
        ips_ejemplo = [
            '192.168.1.100', '192.168.1.101', '192.168.1.102',
            '10.0.0.50', '10.0.0.51', '172.16.0.100'
        ]
        
        user_agents_ejemplo = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)',
            'Mozilla/5.0 (Android 11; Mobile; rv:92.0) Gecko/92.0'
        ]
        
        # Generar registros
        registros_creados = 0
        fecha_inicio = timezone.now() - timedelta(days=dias)
        
        for i in range(cantidad):
            try:
                # Datos aleatorios
                usuario = random.choice(usuarios_ejemplo)
                accion = random.choice(acciones_ejemplo)
                recurso = random.choice(recursos_ejemplo)
                microservicio = random.choice(microservicios_ejemplo)
                
                # Fecha aleatoria en el rango
                fecha_random = fecha_inicio + timedelta(
                    seconds=random.randint(0, int((timezone.now() - fecha_inicio).total_seconds()))
                )
                
                # Generar detalles basados en la acción
                detalle = self._generar_detalle(accion, recurso)
                
                # Determinar éxito (90% exitosas)
                exito = random.random() < 0.9
                codigo_estado = random.choice([200, 201, 204]) if exito else random.choice([400, 401, 403, 404, 500])
                
                # Duración aleatoria
                duracion_ms = random.randint(50, 5000)
                
                # Criticidad basada en acción y éxito
                criticidad = self._determinar_criticidad(accion, exito)
                
                # Crear registro
                actividad = ActividadSistema.objects.create(
                    usuario_id=usuario['id'],
                    usuario_email=usuario['email'],
                    accion=accion,
                    recurso=recurso,
                    recurso_id=str(uuid.uuid4()) if random.random() < 0.7 else None,
                    detalle=detalle,
                    fecha_hora=fecha_random,
                    ip_address=random.choice(ips_ejemplo),
                    user_agent=random.choice(user_agents_ejemplo),
                    session_id=f"session_{random.randint(1000, 9999)}",
                    exito=exito,
                    codigo_estado=codigo_estado,
                    mensaje_error=self._generar_error() if not exito else None,
                    duracion_ms=duracion_ms,
                    microservicio=microservicio,
                    criticidad=criticidad,
                    context={
                        'endpoint': f'/api/{recurso.lower()}/',
                        'method': self._mapear_accion_metodo(accion),
                        'generated': True
                    },
                    tags=['seed_data', f'microservicio_{microservicio.lower()}']
                )
                
                registros_creados += 1
                
                if registros_creados % 50 == 0:
                    self.stdout.write(f'Creados {registros_creados} registros...')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creando registro {i}: {str(e)}'))
        
        # Generar algunos registros específicos de interés
        self._generar_registros_especiales(auditoria_service)
        
        self.stdout.write(self.style.SUCCESS(
            f'¡Éxito! Se crearon {registros_creados} registros de auditoría'
        ))
        
        # Mostrar estadísticas
        total_registros = ActividadSistema.objects.count()
        registros_exitosos = ActividadSistema.objects.filter(exito=True).count()
        registros_fallidos = ActividadSistema.objects.filter(exito=False).count()
        
        self.stdout.write('\n--- Estadísticas ---')
        self.stdout.write(f'Total de registros: {total_registros}')
        self.stdout.write(f'Exitosos: {registros_exitosos}')
        self.stdout.write(f'Fallidos: {registros_fallidos}')
        self.stdout.write(f'Tasa de éxito: {(registros_exitosos/total_registros)*100:.1f}%')
    
    def _generar_detalle(self, accion, recurso):
        """Generar detalle basado en acción y recurso"""
        detalles_base = {
            'CREATE': {
                'USERS': {'action': 'create_user', 'fields': ['name', 'email', 'role']},
                'DOCUMENTS': {'action': 'upload_document', 'file_type': 'pdf', 'size_mb': random.randint(1, 10)},
                'PAYMENTS': {'action': 'create_payment', 'amount': random.randint(100, 5000), 'currency': 'COP'},
            },
            'READ': {
                'USERS': {'action': 'list_users', 'page': random.randint(1, 10)},
                'DOCUMENTS': {'action': 'download_document', 'document_type': random.choice(['certificate', 'transcript', 'diploma'])},
                'REPORTS': {'action': 'generate_report', 'report_type': random.choice(['attendance', 'payments', 'grades'])},
            },
            'UPDATE': {
                'USERS': {'action': 'update_profile', 'fields': ['phone', 'address']},
                'PAYMENTS': {'action': 'update_payment_status', 'status': random.choice(['pending', 'approved', 'rejected'])},
            },
            'DELETE': {
                'USERS': {'action': 'delete_user', 'reason': 'account_closure'},
                'DOCUMENTS': {'action': 'delete_document', 'reason': 'expired'},
            },
            'LOGIN': {
                'AUTH': {'action': 'user_login', 'method': random.choice(['password', '2fa', 'sso'])},
            },
            'LOGOUT': {
                'AUTH': {'action': 'user_logout', 'session_duration': random.randint(300, 7200)},
            }
        }
        
        return detalles_base.get(accion, {}).get(recurso, {'action': f'{accion.lower()}_{recurso.lower()}'})
    
    def _determinar_criticidad(self, accion, exito):
        """Determinar criticidad basada en acción y éxito"""
        if not exito:
            if accion in ['DELETE', 'ACCESS_DENIED']:
                return 'HIGH'
            elif accion in ['CREATE', 'UPDATE']:
                return 'MEDIUM'
            else:
                return 'LOW'
        else:
            if accion in ['DELETE']:
                return 'MEDIUM'
            elif accion in ['CREATE', 'UPDATE']:
                return 'LOW'
            else:
                return None
    
    def _generar_error(self):
        """Generar mensaje de error aleatorio"""
        errores = [
            'Unauthorized access attempt',
            'Invalid credentials provided',
            'Resource not found',
            'Permission denied',
            'Database connection error',
            'File upload failed',
            'Validation error',
            'Session expired',
            'Rate limit exceeded',
            'Internal server error'
        ]
        return random.choice(errores)
    
    def _mapear_accion_metodo(self, accion):
        """Mapear acción a método HTTP"""
        mapeo = {
            'CREATE': 'POST',
            'READ': 'GET',
            'UPDATE': 'PUT',
            'DELETE': 'DELETE',
            'LOGIN': 'POST',
            'LOGOUT': 'POST',
            'UPLOAD': 'POST',
            'DOWNLOAD': 'GET',
            'EXPORT': 'GET',
            'IMPORT': 'POST'
        }
        return mapeo.get(accion, 'GET')
    
    def _generar_registros_especiales(self, auditoria_service):
        """Generar algunos registros especiales de interés"""
        self.stdout.write('Generando registros especiales...')
        
        # Intentos de login fallidos consecutivos
        for i in range(5):
            auditoria_service.registrar_intento_login(
                usuario_email='admin@pontificia.edu',
                exito=False,
                ip_address='192.168.1.999',
                detalle={'reason': 'invalid_password', 'attempt': i+1}
            )
        
        # Actividad sospechosa: múltiples descargas
        for i in range(10):
            auditoria_service.registrar_descarga(
                usuario_id=3,
                archivo='documento_confidencial.pdf',
                detalle={'suspicious': True, 'rapid_download': True}
            )
        
        # Cambios importantes en el sistema
        auditoria_service.registrar_cambio_sistema(
            usuario_id=1,
            componente='database',
            accion='backup_created',
            detalle={'backup_size': '2.5GB', 'scheduled': True}
        )
        
        self.stdout.write('Registros especiales creados')