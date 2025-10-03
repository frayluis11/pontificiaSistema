"""
Comando Django para crear usuarios iniciales (seeds)
python manage.py seed_users
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from auth_app.factory import UsuarioFactory
from auth_app.constants import RolUsuario
from auth_app.models import Usuario
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crea usuarios iniciales para el sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Elimina usuarios existentes antes de crear nuevos'
        )
        
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Número total de usuarios a crear (default: 20)'
        )
    
    def handle(self, *args, **options):
        """Ejecuta el comando de creación de usuarios"""
        self.stdout.write('🚀 Iniciando creación de usuarios semilla...')
        
        # Eliminar usuarios existentes si se especifica
        if options['delete_existing']:
            self.stdout.write('🗑️  Eliminando usuarios existentes...')
            Usuario.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('   ✅ Usuarios existentes eliminados')
            )
        
        try:
            with transaction.atomic():
                self._crear_usuarios_semilla(options['count'])
                
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ ¡{options["count"]} usuarios creados exitosamente!'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear usuarios: {str(e)}')
            )
            logger.error(f"Error en seed_users: {str(e)}")
    
    def _crear_usuarios_semilla(self, total_usuarios=20):
        """Crea los usuarios semilla según la distribución especificada"""
        
        # Distribución de roles según especificaciones
        # 5 ADMIN, 5 DOCENTE, 3 RRHH, 3 CONTABILIDAD, 4 ESTUDIANTES
        usuarios_a_crear = [
            # 5 Administradores
            *[RolUsuario.ADMIN] * 5,
            # 5 Docentes
            *[RolUsuario.DOCENTE] * 5,
            # 3 RRHH
            *[RolUsuario.RRHH] * 3,
            # 3 Contabilidad
            *[RolUsuario.CONTABILIDAD] * 3,
            # 4 Estudiantes
            *[RolUsuario.ESTUDIANTE] * 4,
        ]
        
        # Ajustar si se requiere un número diferente
        if total_usuarios != 20:
            # Calcular distribución proporcional
            admin_count = max(1, (total_usuarios * 5) // 20)
            docente_count = max(1, (total_usuarios * 5) // 20)
            rrhh_count = max(1, (total_usuarios * 3) // 20)
            contab_count = max(1, (total_usuarios * 3) // 20)
            estudiante_count = total_usuarios - admin_count - docente_count - rrhh_count - contab_count
            
            usuarios_a_crear = [
                *[RolUsuario.ADMIN] * admin_count,
                *[RolUsuario.DOCENTE] * docente_count,
                *[RolUsuario.RRHH] * rrhh_count,
                *[RolUsuario.CONTABILIDAD] * contab_count,
                *[RolUsuario.ESTUDIANTE] * max(0, estudiante_count),
            ]
        
        # Datos base para usuarios
        usuarios_data = [
            # Administradores
            {'nombre': 'Carlos', 'apellido': 'Rodríguez', 'dni': '12345678', 'correo': 'carlos.rodriguez@pontificia.edu.pe'},
            {'nombre': 'María', 'apellido': 'González', 'dni': '12345679', 'correo': 'maria.gonzalez@pontificia.edu.pe'},
            {'nombre': 'Luis', 'apellido': 'Martínez', 'dni': '12345680', 'correo': 'luis.martinez@pontificia.edu.pe'},
            {'nombre': 'Ana', 'apellido': 'López', 'dni': '12345681', 'correo': 'ana.lopez@pontificia.edu.pe'},
            {'nombre': 'Pedro', 'apellido': 'Sánchez', 'dni': '12345682', 'correo': 'pedro.sanchez@pontificia.edu.pe'},
            
            # Docentes
            {'nombre': 'Elena', 'apellido': 'Ramírez', 'dni': '23456789', 'correo': 'elena.ramirez@pontificia.edu.pe'},
            {'nombre': 'Jorge', 'apellido': 'Torres', 'dni': '23456790', 'correo': 'jorge.torres@pontificia.edu.pe'},
            {'nombre': 'Carmen', 'apellido': 'Flores', 'dni': '23456791', 'correo': 'carmen.flores@pontificia.edu.pe'},
            {'nombre': 'Roberto', 'apellido': 'Morales', 'dni': '23456792', 'correo': 'roberto.morales@pontificia.edu.pe'},
            {'nombre': 'Patricia', 'apellido': 'Ruiz', 'dni': '23456793', 'correo': 'patricia.ruiz@pontificia.edu.pe'},
            
            # RRHH
            {'nombre': 'Fernando', 'apellido': 'Castro', 'dni': '34567890', 'correo': 'fernando.castro@pontificia.edu.pe'},
            {'nombre': 'Silvia', 'apellido': 'Herrera', 'dni': '34567891', 'correo': 'silvia.herrera@pontificia.edu.pe'},
            {'nombre': 'Manuel', 'apellido': 'Vega', 'dni': '34567892', 'correo': 'manuel.vega@pontificia.edu.pe'},
            
            # Contabilidad
            {'nombre': 'Rosa', 'apellido': 'Jiménez', 'dni': '45678901', 'correo': 'rosa.jimenez@pontificia.edu.pe'},
            {'nombre': 'Andrés', 'apellido': 'Peña', 'dni': '45678902', 'correo': 'andres.pena@pontificia.edu.pe'},
            {'nombre': 'Lucía', 'apellido': 'Ortega', 'dni': '45678903', 'correo': 'lucia.ortega@pontificia.edu.pe'},
            
            # Estudiantes
            {'nombre': 'Diego', 'apellido': 'Mendoza', 'dni': '56789012', 'correo': 'diego.mendoza@estudiante.pontificia.edu.pe'},
            {'nombre': 'Sofía', 'apellido': 'Vargas', 'dni': '56789013', 'correo': 'sofia.vargas@estudiante.pontificia.edu.pe'},
            {'nombre': 'Javier', 'apellido': 'Reyes', 'dni': '56789014', 'correo': 'javier.reyes@estudiante.pontificia.edu.pe'},
            {'nombre': 'Isabella', 'apellido': 'Cruz', 'dni': '56789015', 'correo': 'isabella.cruz@estudiante.pontificia.edu.pe'},
        ]
        
        # Crear usuarios
        for i, rol in enumerate(usuarios_a_crear):
            if i < len(usuarios_data):
                data = usuarios_data[i].copy()
            else:
                # Generar datos adicionales si se necesitan más usuarios
                data = {
                    'nombre': f'Usuario{i+1}',
                    'apellido': f'Apellido{i+1}',
                    'dni': f'{10000000 + i}',
                    'correo': f'usuario{i+1}@pontificia.edu.pe'
                }
            
            # Agregar contraseña más fuerte por defecto
            data['password'] = 'PontificiAuth2024!'  # Contraseña más segura
            
            try:
                # Usar el factory según el rol con parámetros específicos
                if rol == RolUsuario.ADMIN:
                    usuario = UsuarioFactory.crear_admin(
                        dni=data['dni'],
                        nombre=data['nombre'],
                        apellido=data['apellido'],
                        correo=data['correo'],
                        password=data['password']
                    )
                elif rol == RolUsuario.DOCENTE:
                    usuario = UsuarioFactory.crear_docente(
                        dni=data['dni'],
                        nombre=data['nombre'],
                        apellido=data['apellido'],
                        correo=data['correo'],
                        password=data['password']
                    )
                elif rol == RolUsuario.ESTUDIANTE:
                    usuario = UsuarioFactory.crear_estudiante(
                        dni=data['dni'],
                        nombre=data['nombre'],
                        apellido=data['apellido'],
                        correo=data['correo'],
                        password=data['password']
                    )
                else:
                    # Para RRHH y CONTABILIDAD crear manualmente con rol específico
                    data['rol'] = rol
                    usuario = UsuarioFactory.crear_usuario(**data)
                
                self.stdout.write(
                    f'   ✅ Creado: {usuario.get_full_name()} ({usuario.get_rol_display()}) - DNI: {usuario.dni}'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'   ❌ Error creando usuario {data["nombre"]} {data["apellido"]}: {str(e)}'
                    )
                )
        
        # Mostrar resumen
        self._mostrar_resumen()
    
    def _mostrar_resumen(self):
        """Muestra un resumen de los usuarios creados"""
        self.stdout.write('\n📊 RESUMEN DE USUARIOS CREADOS:')
        self.stdout.write('=' * 50)
        
        for rol_value, rol_name in RolUsuario.choices:
            count = Usuario.objects.filter(rol=rol_value).count()
            if count > 0:
                self.stdout.write(f'   {rol_name}: {count} usuarios')
        
        total = Usuario.objects.count()
        activos = Usuario.objects.filter(estado=True).count()
        
        self.stdout.write('=' * 50)
        self.stdout.write(f'   TOTAL: {total} usuarios')
        self.stdout.write(f'   ACTIVOS: {activos} usuarios')
        self.stdout.write('')
        self.stdout.write('🔑 Contraseña por defecto para todos: PontificiAuth2024!')
        self.stdout.write('⚠️  Recuerda cambiar las contraseñas en producción!')
        self.stdout.write('')