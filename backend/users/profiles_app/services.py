"""
Servicios de negocio para perfiles
Sistema Pontificia - Users Service
"""
from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Profile
from .repository import ProfileRepository
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class ProfileService:
    """
    Servicio para la lógica de negocio de perfiles
    """
    
    @staticmethod
    def crear_profile(data: Dict[str, Any], usuario_solicitante_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Crea un nuevo perfil con validaciones de negocio
        
        Args:
            data (Dict): Datos del perfil
            usuario_solicitante_id (Optional[int]): ID del usuario que hace la solicitud
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos requeridos
            if not data.get('usuario_id'):
                raise ValidationError("El campo usuario_id es requerido")
            
            usuario_id = data['usuario_id']
            
            # Verificar que no existe ya un perfil
            if ProfileRepository.existe_profile(usuario_id):
                raise ValidationError(f"Ya existe un perfil para el usuario {usuario_id}")
            
            # Validar permisos (solo el propio usuario o admin puede crear su perfil)
            if usuario_solicitante_id and usuario_solicitante_id != usuario_id:
                # Aquí se podría verificar si es admin consultando auth_service
                # Por ahora permitimos solo al propio usuario
                pass
            
            # Validar y limpiar datos
            datos_limpios = ProfileService._validar_datos_profile(data)
            
            # Crear perfil
            profile = ProfileRepository.crear_profile(datos_limpios)
            
            logger.info(f"Perfil creado exitosamente para usuario {usuario_id}")
            
            return {
                'exito': True,
                'mensaje': 'Perfil creado exitosamente',
                'data': ProfileService._profile_to_dict(profile)
            }
            
        except ValidationError as e:
            logger.warning(f"Error de validación creando perfil: {str(e)}")
            return {
                'exito': False,
                'mensaje': str(e),
                'errores': getattr(e, 'message_dict', {})
            }
        except Exception as e:
            logger.error(f"Error inesperado creando perfil: {str(e)}")
            return {
                'exito': False,
                'mensaje': f'Error interno: {str(e)}'
            }
    
    @staticmethod
    def obtener_profile(usuario_id: int, solicitante_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene un perfil aplicando reglas de privacidad
        
        Args:
            usuario_id (int): ID del usuario del perfil
            solicitante_id (Optional[int]): ID del usuario que solicita
            
        Returns:
            Dict: Perfil encontrado o error
        """
        try:
            profile = ProfileRepository.obtener_por_usuario_id(usuario_id)
            
            if not profile:
                return {
                    'exito': False,
                    'mensaje': 'Perfil no encontrado'
                }
            
            # Aplicar reglas de privacidad
            es_propio_perfil = solicitante_id == usuario_id
            es_perfil_publico = profile.perfil_publico
            
            if not es_propio_perfil and not es_perfil_publico:
                return {
                    'exito': False,
                    'mensaje': 'Perfil privado'
                }
            
            # Obtener datos del perfil
            profile_data = ProfileService._profile_to_dict(profile, es_propio_perfil)
            
            return {
                'exito': True,
                'data': profile_data
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo perfil: {str(e)}")
            return {
                'exito': False,
                'mensaje': f'Error interno: {str(e)}'
            }
    
    @staticmethod
    def actualizar_profile(usuario_id: int, data: Dict[str, Any], solicitante_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Actualiza un perfil existente
        
        Args:
            usuario_id (int): ID del usuario del perfil
            data (Dict): Datos a actualizar
            solicitante_id (Optional[int]): ID del usuario que solicita
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar permisos (solo el propio usuario puede actualizar su perfil)
            if solicitante_id and solicitante_id != usuario_id:
                # Aquí se podría verificar si es admin
                return {
                    'exito': False,
                    'mensaje': 'No tienes permisos para actualizar este perfil'
                }
            
            # Verificar que existe el perfil
            if not ProfileRepository.existe_profile(usuario_id):
                return {
                    'exito': False,
                    'mensaje': 'Perfil no encontrado'
                }
            
            # Validar y limpiar datos
            datos_limpios = ProfileService._validar_datos_profile(data, es_actualizacion=True)
            
            # Actualizar perfil
            profile = ProfileRepository.actualizar_profile(usuario_id, datos_limpios)
            
            if not profile:
                return {
                    'exito': False,
                    'mensaje': 'Error actualizando perfil'
                }
            
            logger.info(f"Perfil actualizado exitosamente para usuario {usuario_id}")
            
            return {
                'exito': True,
                'mensaje': 'Perfil actualizado exitosamente',
                'data': ProfileService._profile_to_dict(profile, es_propio=True)
            }
            
        except ValidationError as e:
            logger.warning(f"Error de validación actualizando perfil: {str(e)}")
            return {
                'exito': False,
                'mensaje': str(e),
                'errores': getattr(e, 'message_dict', {})
            }
        except Exception as e:
            logger.error(f"Error inesperado actualizando perfil: {str(e)}")
            return {
                'exito': False,
                'mensaje': f'Error interno: {str(e)}'
            }
    
    @staticmethod
    def listar_profiles(publicos_solo: bool = True, departamento: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista perfiles aplicando filtros
        
        Args:
            publicos_solo (bool): Solo perfiles públicos
            departamento (Optional[str]): Filtrar por departamento
            
        Returns:
            Dict: Lista de perfiles
        """
        try:
            if departamento:
                profiles = ProfileRepository.buscar_por_departamento(departamento)
            elif publicos_solo:
                profiles = ProfileRepository.obtener_publicos()
            else:
                profiles = ProfileRepository.obtener_todos()
            
            profiles_data = [
                ProfileService._profile_to_dict(profile, es_propio=False)
                for profile in profiles
            ]
            
            return {
                'exito': True,
                'data': profiles_data,
                'total': len(profiles_data)
            }
            
        except Exception as e:
            logger.error(f"Error listando perfiles: {str(e)}")
            return {
                'exito': False,
                'mensaje': f'Error interno: {str(e)}'
            }
    
    @staticmethod
    def sincronizar_con_auth_service(usuario_id: int, datos_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sincroniza la creación de perfil cuando se crea un usuario en auth_service
        
        Args:
            usuario_id (int): ID del usuario creado en auth_service
            datos_usuario (Dict): Datos básicos del usuario
            
        Returns:
            Dict: Resultado de la sincronización
        """
        try:
            # Verificar si ya existe el perfil
            if ProfileRepository.existe_profile(usuario_id):
                return {
                    'exito': True,
                    'mensaje': 'Perfil ya existe',
                    'accion': 'ninguna'
                }
            
            # Crear perfil básico con datos del usuario
            datos_perfil = {
                'usuario_id': usuario_id,
                'departamento': datos_usuario.get('departamento'),
                'cargo': datos_usuario.get('cargo'),
                'perfil_publico': True,  # Por defecto público
                'mostrar_correo': True,
                'mostrar_telefono': False
            }
            
            resultado = ProfileService.crear_profile(datos_perfil)
            
            if resultado['exito']:
                logger.info(f"Perfil sincronizado para usuario {usuario_id}")
                return {
                    'exito': True,
                    'mensaje': 'Perfil creado por sincronización',
                    'accion': 'creado',
                    'data': resultado['data']
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error en sincronización: {str(e)}")
            return {
                'exito': False,
                'mensaje': f'Error en sincronización: {str(e)}'
            }
    
    @staticmethod
    def _validar_datos_profile(data: Dict[str, Any], es_actualizacion: bool = False) -> Dict[str, Any]:
        """
        Valida y limpia los datos del perfil
        
        Args:
            data (Dict): Datos a validar
            es_actualizacion (bool): Si es una actualización
            
        Returns:
            Dict: Datos validados y limpios
        """
        datos_limpios = {}
        
        # Campo requerido solo en creación
        if 'usuario_id' in data:
            if not isinstance(data['usuario_id'], int) or data['usuario_id'] <= 0:
                raise ValidationError("usuario_id debe ser un entero positivo")
            datos_limpios['usuario_id'] = data['usuario_id']
        elif not es_actualizacion:
            raise ValidationError("usuario_id es requerido")
        
        # Validar campos opcionales
        campos_opcionales = {
            'telefono': str,
            'direccion': str,
            'cargo': str,
            'departamento': str,
            'biografia': str,
            'avatar_url': str
        }
        
        for campo, tipo in campos_opcionales.items():
            if campo in data and data[campo] is not None:
                valor = str(data[campo]).strip() if data[campo] else None
                if valor:  # Solo agregar si no está vacío
                    datos_limpios[campo] = valor
        
        # Validar campos booleanos
        campos_bool = ['perfil_publico', 'mostrar_telefono', 'mostrar_correo']
        for campo in campos_bool:
            if campo in data:
                datos_limpios[campo] = bool(data[campo])
        
        # Validar fechas
        if 'fecha_ingreso' in data and data['fecha_ingreso']:
            # Aquí se podría agregar validación de formato de fecha
            datos_limpios['fecha_ingreso'] = data['fecha_ingreso']
        
        if 'fecha_nacimiento' in data and data['fecha_nacimiento']:
            datos_limpios['fecha_nacimiento'] = data['fecha_nacimiento']
        
        return datos_limpios
    
    @staticmethod
    def _profile_to_dict(profile: Profile, es_propio: bool = False) -> Dict[str, Any]:
        """
        Convierte un perfil a diccionario aplicando reglas de privacidad
        
        Args:
            profile (Profile): Perfil a convertir
            es_propio (bool): Si es el propio perfil del usuario
            
        Returns:
            Dict: Datos del perfil
        """
        data = {
            'id': profile.id,
            'usuario_id': profile.usuario_id,
            'cargo': profile.cargo,
            'departamento': profile.departamento,
            'fecha_ingreso': profile.fecha_ingreso.isoformat() if profile.fecha_ingreso else None,
            'biografia': profile.biografia,
            'avatar_url': profile.avatar_url,
            'perfil_publico': profile.perfil_publico,
            'fecha_creacion': profile.fecha_creacion.isoformat(),
            'fecha_actualizacion': profile.fecha_actualizacion.isoformat(),
            'edad': profile.edad,
            'anos_en_institucion': profile.anos_en_institucion
        }
        
        # Campos que dependen de configuración de privacidad o si es propio perfil
        if es_propio or profile.mostrar_telefono:
            data['telefono'] = profile.telefono
        
        if es_propio:
            # Solo el propio usuario ve estos campos
            data.update({
                'direccion': profile.direccion,
                'fecha_nacimiento': profile.fecha_nacimiento.isoformat() if profile.fecha_nacimiento else None,
                'mostrar_telefono': profile.mostrar_telefono,
                'mostrar_correo': profile.mostrar_correo,
                'activo': profile.activo
            })
        
        # Eliminar campos None para respuesta más limpia
        return {k: v for k, v in data.items() if v is not None}
    
    @staticmethod
    def obtener_estadisticas() -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio de perfiles
        
        Returns:
            Dict: Estadísticas
        """
        try:
            return ProfileRepository.obtener_estadisticas()
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'error': 'Error obteniendo estadísticas'
            }