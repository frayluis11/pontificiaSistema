"""
Repository para operaciones de perfiles
Implementa el patrón Repository para separar la lógica de acceso a datos
"""
from typing import Optional, Dict, Any, List
from django.db import transaction, IntegrityError
from django.db.models import QuerySet, Q
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from .models import Profile
import logging

logger = logging.getLogger(__name__)


class ProfileRepository:
    """
    Repository para operaciones CRUD de perfiles
    """
    
    @staticmethod
    def crear_profile(data: Dict[str, Any]) -> Profile:
        """
        Crea un nuevo perfil
        
        Args:
            data (Dict): Datos del perfil
            
        Returns:
            Profile: Perfil creado
            
        Raises:
            ValidationError: Si los datos son inválidos
        """
        try:
            with transaction.atomic():
                profile = Profile.objects.create(
                    usuario_id=data['usuario_id'],
                    telefono=data.get('telefono'),
                    direccion=data.get('direccion'),
                    cargo=data.get('cargo'),
                    departamento=data.get('departamento'),
                    fecha_ingreso=data.get('fecha_ingreso'),
                    biografia=data.get('biografia'),
                    avatar_url=data.get('avatar_url'),
                    fecha_nacimiento=data.get('fecha_nacimiento'),
                    perfil_publico=data.get('perfil_publico', True),
                    mostrar_telefono=data.get('mostrar_telefono', False),
                    mostrar_correo=data.get('mostrar_correo', True),
                )
                
                logger.info(f"Perfil creado exitosamente para usuario {profile.usuario_id}")
                return profile
                
        except IntegrityError as e:
            if 'usuario_id' in str(e):
                raise ValidationError(f"Ya existe un perfil para el usuario {data['usuario_id']}")
            raise ValidationError(f"Error de integridad: {str(e)}")
        except Exception as e:
            logger.error(f"Error creando perfil: {str(e)}")
            raise ValidationError(f"Error al crear perfil: {str(e)}")
    
    @staticmethod
    def obtener_por_usuario_id(usuario_id: int) -> Optional[Profile]:
        """
        Obtiene un perfil por ID de usuario
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            Optional[Profile]: Perfil encontrado o None
        """
        try:
            return Profile.objects.get(usuario_id=usuario_id, activo=True)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo perfil por usuario_id {usuario_id}: {str(e)}")
            return None
    
    @staticmethod
    def obtener_por_id(profile_id: int) -> Optional[Profile]:
        """
        Obtiene un perfil por ID
        
        Args:
            profile_id (int): ID del perfil
            
        Returns:
            Optional[Profile]: Perfil encontrado o None
        """
        try:
            return Profile.objects.get(id=profile_id, activo=True)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo perfil por ID {profile_id}: {str(e)}")
            return None
    
    @staticmethod
    def actualizar_profile(usuario_id: int, data: Dict[str, Any]) -> Optional[Profile]:
        """
        Actualiza un perfil existente
        
        Args:
            usuario_id (int): ID del usuario
            data (Dict): Datos a actualizar
            
        Returns:
            Optional[Profile]: Perfil actualizado o None
        """
        try:
            with transaction.atomic():
                profile = ProfileRepository.obtener_por_usuario_id(usuario_id)
                if not profile:
                    return None
                
                # Actualizar campos
                campos_actualizables = [
                    'telefono', 'direccion', 'cargo', 'departamento', 'fecha_ingreso',
                    'biografia', 'avatar_url', 'fecha_nacimiento', 'perfil_publico',
                    'mostrar_telefono', 'mostrar_correo'
                ]
                
                for campo in campos_actualizables:
                    if campo in data:
                        setattr(profile, campo, data[campo])
                
                profile.fecha_actualizacion = timezone.now()
                profile.save()
                
                logger.info(f"Perfil actualizado exitosamente para usuario {usuario_id}")
                return profile
                
        except Exception as e:
            logger.error(f"Error actualizando perfil: {str(e)}")
            raise ValidationError(f"Error al actualizar perfil: {str(e)}")
    
    @staticmethod
    def eliminar_profile(usuario_id: int) -> bool:
        """
        Elimina (desactiva) un perfil
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            bool: True si se eliminó, False si no existía
        """
        try:
            profile = ProfileRepository.obtener_por_usuario_id(usuario_id)
            if profile:
                profile.activo = False
                profile.save()
                logger.info(f"Perfil desactivado para usuario {usuario_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando perfil: {str(e)}")
            return False
    
    @staticmethod
    def obtener_todos(incluir_inactivos: bool = False) -> QuerySet[Profile]:
        """
        Obtiene todos los perfiles
        
        Args:
            incluir_inactivos (bool): Incluir perfiles inactivos
            
        Returns:
            QuerySet[Profile]: Perfiles encontrados
        """
        try:
            if incluir_inactivos:
                return Profile.objects.all().order_by('-fecha_creacion')
            return Profile.objects.filter(activo=True).order_by('-fecha_creacion')
        except Exception as e:
            logger.error(f"Error obteniendo todos los perfiles: {str(e)}")
            return Profile.objects.none()
    
    @staticmethod
    def obtener_publicos() -> QuerySet[Profile]:
        """
        Obtiene perfiles públicos activos
        
        Returns:
            QuerySet[Profile]: Perfiles públicos
        """
        try:
            return Profile.objects.filter(
                activo=True,
                perfil_publico=True
            ).order_by('-fecha_creacion')
        except Exception as e:
            logger.error(f"Error obteniendo perfiles públicos: {str(e)}")
            return Profile.objects.none()
    
    @staticmethod
    def buscar_por_departamento(departamento: str) -> QuerySet[Profile]:
        """
        Busca perfiles por departamento
        
        Args:
            departamento (str): Nombre del departamento
            
        Returns:
            QuerySet[Profile]: Perfiles encontrados
        """
        try:
            return Profile.objects.filter(
                activo=True,
                departamento__icontains=departamento
            ).order_by('-fecha_creacion')
        except Exception as e:
            logger.error(f"Error buscando por departamento: {str(e)}")
            return Profile.objects.none()
    
    @staticmethod
    def buscar_perfiles(termino: str) -> QuerySet[Profile]:
        """
        Busca perfiles por término general
        
        Args:
            termino (str): Término de búsqueda
            
        Returns:
            QuerySet[Profile]: Perfiles encontrados
        """
        try:
            return Profile.objects.filter(
                Q(cargo__icontains=termino) |
                Q(departamento__icontains=termino) |
                Q(biografia__icontains=termino),
                activo=True
            ).order_by('-fecha_creacion')
        except Exception as e:
            logger.error(f"Error en búsqueda de perfiles: {str(e)}")
            return Profile.objects.none()
    
    @staticmethod
    def existe_profile(usuario_id: int) -> bool:
        """
        Verifica si existe un perfil para un usuario
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            bool: True si existe, False si no
        """
        try:
            return Profile.objects.filter(usuario_id=usuario_id, activo=True).exists()
        except Exception as e:
            logger.error(f"Error verificando existencia de perfil: {str(e)}")
            return False
    
    @staticmethod
    def obtener_estadisticas() -> Dict[str, Any]:
        """
        Obtiene estadísticas de perfiles
        
        Returns:
            Dict: Estadísticas
        """
        try:
            total_profiles = Profile.objects.filter(activo=True).count()
            profiles_publicos = Profile.objects.filter(activo=True, perfil_publico=True).count()
            profiles_con_telefono = Profile.objects.filter(
                activo=True, 
                telefono__isnull=False
            ).exclude(telefono='').count()
            
            departamentos = Profile.objects.filter(
                activo=True,
                departamento__isnull=False
            ).exclude(departamento='').values_list('departamento', flat=True).distinct()
            
            return {
                'total_profiles': total_profiles,
                'profiles_publicos': profiles_publicos,
                'profiles_con_telefono': profiles_con_telefono,
                'total_departamentos': len(list(departamentos)),
                'departamentos': list(departamentos)
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'total_profiles': 0,
                'profiles_publicos': 0,
                'profiles_con_telefono': 0,
                'total_departamentos': 0,
                'departamentos': []
            }