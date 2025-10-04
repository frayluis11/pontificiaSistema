"""
Repositorio y Factory para el modelo Usuario
Sistema Pontificia - Auth Service
"""
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.db.models import QuerySet, Q
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from .models import Usuario, HistorialLogin, SesionUsuario
from django.utils import timezone
import secrets
import string


class UsuarioRepository:
    """
    Repositorio para operaciones CRUD del modelo Usuario
    Implementa el patrón Repository para separar la lógica de negocio del acceso a datos
    """
    
    @staticmethod
    def crear_usuario(data):
        """Crear un nuevo usuario con validaciones"""
        try:
            with transaction.atomic():
                # Validar datos requeridos
                if not data.get('correo'):
                    raise ValidationError("El correo es requerido")
                if not data.get('dni'):
                    raise ValidationError("El DNI es requerido")
                if not data.get('nombre'):
                    raise ValidationError("El nombre es requerido")
                if not data.get('apellido'):
                    raise ValidationError("El apellido es requerido")
                
                # Verificar unicidad de correo y DNI
                if Usuario.objects.filter(correo=data['correo']).exists():
                    raise ValidationError("Ya existe un usuario con este correo")
                if Usuario.objects.filter(dni=data['dni']).exists():
                    raise ValidationError("Ya existe un usuario con este DNI")
                
                # Crear usuario
                usuario = Usuario.objects.create_user(
                    correo=data['correo'],
                    dni=data['dni'],
                    nombre=data['nombre'],
                    apellido=data['apellido'],
                    password=data.get('password'),
                    telefono=data.get('telefono'),
                    rol=data.get('rol', Usuario.ROL_ESTUDIANTE),
                    estado=data.get('estado', Usuario.ESTADO_PENDIENTE),
                    departamento=data.get('departamento'),
                    cargo=data.get('cargo'),
                    avatar=data.get('avatar')
                )
                
                return usuario
                
        except Exception as e:
            raise ValidationError(f"Error al crear usuario: {str(e)}")
    
    @staticmethod
    def obtener_por_id(usuario_id: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su ID
        
        Args:
            usuario_id (str): ID del usuario
            
        Returns:
            Usuario|None: Instancia del usuario o None si no existe
        """
        try:
            return Usuario.objects.get(id=usuario_id)
        except ObjectDoesNotExist:
            return None
    
    @staticmethod
    def obtener_por_dni(dni: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su DNI
        
        Args:
            dni (str): DNI del usuario
            
        Returns:
            Usuario|None: Instancia del usuario o None si no existe
        """
        try:
            return Usuario.objects.get(dni=dni)
        except ObjectDoesNotExist:
            return None
    
    @staticmethod
    def obtener_por_correo(correo: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su correo electrónico
        
        Args:
            correo (str): Correo electrónico del usuario
            
        Returns:
            Usuario|None: Instancia del usuario o None si no existe
        """
        try:
            return Usuario.objects.get(correo=correo)
        except ObjectDoesNotExist:
            return None
    
    @staticmethod
    def obtener_todos() -> QuerySet[Usuario]:
        """
        Obtiene todos los usuarios
        
        Returns:
            QuerySet[Usuario]: QuerySet con todos los usuarios
        """
        return Usuario.objects.all()
    
    @staticmethod
    def obtener_activos() -> QuerySet[Usuario]:
        """
        Obtiene todos los usuarios activos
        
        Returns:
            QuerySet[Usuario]: QuerySet con usuarios activos
        """
        return Usuario.objects.filter(
            estado=Usuario.ESTADO_ACTIVO,
            is_active=True
        )
    
    @staticmethod
    def obtener_por_rol(rol: str) -> QuerySet[Usuario]:
        """
        Obtiene usuarios por rol
        
        Args:
            rol (str): Rol a filtrar
            
        Returns:
            QuerySet[Usuario]: QuerySet con usuarios del rol especificado
        """
        return Usuario.objects.filter(rol=rol)
    
    @staticmethod
    def obtener_por_estado(estado: str) -> QuerySet[Usuario]:
        """
        Obtiene usuarios por estado
        
        Args:
            estado (str): Estado a filtrar
            
        Returns:
            QuerySet[Usuario]: QuerySet con usuarios del estado especificado
        """
        return Usuario.objects.filter(estado=estado)
    
    @staticmethod
    def buscar_usuarios(termino: str) -> QuerySet[Usuario]:
        """
        Busca usuarios por nombre, apellido, DNI o correo
        
        Args:
            termino (str): Término de búsqueda
            
        Returns:
            QuerySet[Usuario]: QuerySet con usuarios que coinciden con la búsqueda
        """
        return Usuario.objects.filter(
            Q(nombre__icontains=termino) |
            Q(apellido__icontains=termino) |
            Q(dni__icontains=termino) |
            Q(correo__icontains=termino)
        )
    
    @staticmethod
    def existe_dni(dni: str) -> bool:
        """
        Verifica si existe un usuario con el DNI especificado
        
        Args:
            dni (str): DNI a verificar
            
        Returns:
            bool: True si existe, False si no
        """
        return Usuario.objects.filter(dni=dni).exists()
    
    @staticmethod
    def existe_correo(correo: str) -> bool:
        """
        Verifica si existe un usuario con el correo especificado
        
        Args:
            correo (str): Correo a verificar
            
        Returns:
            bool: True si existe, False si no
        """
        return Usuario.objects.filter(correo=correo).exists()
    
    @staticmethod
    def actualizar_usuario(usuario_id: str, datos: Dict[str, Any]) -> Optional[Usuario]:
        """
        Actualiza un usuario existente
        
        Args:
            usuario_id (str): ID del usuario a actualizar
            datos (Dict): Datos a actualizar
            
        Returns:
            Usuario|None: Usuario actualizado o None si no existe
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            for campo, valor in datos.items():
                setattr(usuario, campo, valor)
            usuario.save()
            return usuario
        except ObjectDoesNotExist:
            return None
    
    @staticmethod
    def eliminar_usuario(usuario_id: str) -> bool:
        """
        Elimina un usuario (soft delete cambiando estado)
        
        Args:
            usuario_id (str): ID del usuario a eliminar
            
        Returns:
            bool: True si se eliminó, False si no existe
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            usuario.desactivar()
            return True
        except ObjectDoesNotExist:
            return False
    
    @staticmethod
    def cambiar_estado_usuario(usuario_id: str, nuevo_estado: str) -> Optional[Usuario]:
        """
        Cambia el estado de un usuario
        
        Args:
            usuario_id (str): ID del usuario
            nuevo_estado (str): Nuevo estado
            
        Returns:
            Usuario|None: Usuario actualizado o None si no existe
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            if nuevo_estado == Usuario.ESTADO_ACTIVO:
                usuario.activar()
            elif nuevo_estado == Usuario.ESTADO_INACTIVO:
                usuario.desactivar()
            elif nuevo_estado == Usuario.ESTADO_SUSPENDIDO:
                usuario.suspender()
            elif nuevo_estado == Usuario.ESTADO_BLOQUEADO:
                usuario.bloquear()
            
            return usuario
        except ObjectDoesNotExist:
            return None
    
    @staticmethod
    def actualizar_ultimo_acceso(usuario_id: str) -> Optional[Usuario]:
        """
        Actualiza la fecha del último acceso de un usuario
        
        Args:
            usuario_id (str): ID del usuario
            
        Returns:
            Usuario|None: Usuario actualizado o None si no existe
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            usuario.actualizar_ultimo_acceso()
            return usuario
        except ObjectDoesNotExist:
            return None
    
    @staticmethod
    def obtener_estadisticas_usuarios() -> Dict[str, int]:
        """
        Obtiene estadísticas de usuarios por rol y estado
        
        Returns:
            Dict: Diccionario con estadísticas
        """
        total_usuarios = Usuario.objects.count()
        usuarios_activos = Usuario.objects.filter(estado=Usuario.ESTADO_ACTIVO).count()
        usuarios_inactivos = Usuario.objects.filter(estado=Usuario.ESTADO_INACTIVO).count()
        
        estadisticas_rol = {}
        for rol, _ in Usuario.ROLES_CHOICES:
            estadisticas_rol[f'total_{rol.lower()}'] = Usuario.objects.filter(rol=rol).count()
        
        return {
            'total_usuarios': total_usuarios,
            'usuarios_activos': usuarios_activos,
            'usuarios_inactivos': usuarios_inactivos,
            **estadisticas_rol
        }


# TokenBlacklist functionality will be implemented later when needed
        # activos del usuario, pero requiere integración con el sistema JWT
        pass