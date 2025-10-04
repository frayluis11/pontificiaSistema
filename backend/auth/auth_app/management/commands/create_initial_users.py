"""
Management command para crear usuarios iniciales (seeds)
Sistema Pontificia - Auth Service
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from auth_app.models import Usuario
from auth_app.factory import UsuarioFactory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crear usuarios iniciales para el sistema Pontificia'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar creación incluso si ya existen usuarios',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )
    
    def handle(self, *args, **options):
        """Ejecutar comando"""
        try:
            # Verificar si ya existen usuarios
            if Usuario.objects.exists() and not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        'Ya existen usuarios en el sistema. Use --force para crear de todas formas.'
                    )
                )
                return
            
            if options['force'] and Usuario.objects.exists():
                self.stdout.write(
                    self.style.WARNING('Limpiando usuarios existentes...')
                )
                Usuario.objects.all().delete()
            
            # Crear usuarios usando la factory
            self.stdout.write('Creando usuarios iniciales...')
            
            usuarios_creados = []
            
            with transaction.atomic():
                # 5 Administradores
                self.stdout.write('📋 Creando 5 administradores...')
                for i in range(5):
                    usuario = UsuarioFactory.crear_usuario_admin()
                    usuarios_creados.append(usuario)
                    if options['verbose']:
                        self.stdout.write(f"  ✓ Admin: {usuario.nombre_completo} ({usuario.correo})")
                
                # 5 Docentes
                self.stdout.write('👨‍🏫 Creando 5 docentes...')
                for i in range(5):
                    usuario = UsuarioFactory.crear_usuario_docente()
                    usuarios_creados.append(usuario)
                    if options['verbose']:
                        self.stdout.write(f"  ✓ Docente: {usuario.nombre_completo} ({usuario.correo})")
                
                # 3 RRHH
                self.stdout.write('👥 Creando 3 usuarios de RRHH...')
                for i in range(3):
                    usuario = UsuarioFactory.crear_usuario_rrhh()
                    usuarios_creados.append(usuario)
                    if options['verbose']:
                        self.stdout.write(f"  ✓ RRHH: {usuario.nombre_completo} ({usuario.correo})")
                
                # 3 Contabilidad
                self.stdout.write('💰 Creando 3 usuarios de contabilidad...')
                for i in range(3):
                    usuario = UsuarioFactory.crear_usuario_contabilidad()
                    usuarios_creados.append(usuario)
                    if options['verbose']:
                        self.stdout.write(f"  ✓ Contabilidad: {usuario.nombre_completo} ({usuario.correo})")
                
                # 4 Estudiantes
                self.stdout.write('🎓 Creando 4 estudiantes...')
                for i in range(4):
                    usuario = UsuarioFactory.crear_usuario_estudiante()
                    usuarios_creados.append(usuario)
                    if options['verbose']:
                        self.stdout.write(f"  ✓ Estudiante: {usuario.nombre_completo} ({usuario.correo})")
            
            # Resumen
            self.stdout.write('\n' + '='*60)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ ¡Creados {len(usuarios_creados)} usuarios exitosamente!'
                )
            )
            
            # Mostrar estadísticas por rol
            roles_stats = {}
            for usuario in usuarios_creados:
                rol = usuario.get_rol_display()
                roles_stats[rol] = roles_stats.get(rol, 0) + 1
            
            self.stdout.write('\n📊 Estadísticas por rol:')
            for rol, cantidad in roles_stats.items():
                self.stdout.write(f"  • {rol}: {cantidad}")
            
            # Mostrar usuarios especiales (admins) con sus credenciales
            self.stdout.write('\n🔑 Usuarios administradores creados:')
            admins = [u for u in usuarios_creados if u.es_admin()]
            for admin in admins:
                self.stdout.write(
                    f"  • {admin.nombre_completo}"
                    f"\n    📧 Email: {admin.correo}"
                    f"\n    🆔 DNI: {admin.dni}"
                    f"\n    🏢 Departamento: {admin.departamento}"
                )
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  IMPORTANTE: Las contraseñas temporales se generaron automáticamente.\n'
                    '   Los usuarios deben cambiarlas en su primer login.'
                )
            )
            
            logger.info(f"Seeds ejecutado exitosamente. Usuarios creados: {len(usuarios_creados)}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando usuarios: {str(e)}')
            )
            logger.error(f"Error en seeds: {str(e)}", exc_info=True)
            raise