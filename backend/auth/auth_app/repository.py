"""
Repositorio para el modelo Usuario
Proporciona una capa de abstracción para las operaciones de base de datos
"""
from typing import List, Optional, Dict, Any
from django.db.models import QuerySet, Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import Usuario, TokenBlacklist


class UsuarioRepository:
    """
    Repositorio para operaciones CRUD del modelo Usuario
    """
    
    @staticmethod
    def crear_usuario(datos_usuario: Dict[str, Any]) -> Usuario:
        """
        Crea un nuevo usuario en la base de datos
        
        Args:
            datos_usuario (Dict): Diccionario con los datos del usuario
            
        Returns:
            Usuario: Instancia del usuario creado
        """
        return Usuario.objects.create_user(**datos_usuario)
    
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


class TokenBlacklistRepository:
    """
    Repositorio para operaciones del blacklist de tokens
    """
    
    @staticmethod
    def agregar_token_blacklist(token: str, usuario: Usuario, razon: str = 'logout') -> TokenBlacklist:
        """
        Agrega un token al blacklist
        
        Args:
            token (str): Token a invalidar
            usuario (Usuario): Usuario propietario del token
            razon (str): Razón de la invalidación
            
        Returns:
            TokenBlacklist: Instancia del token en blacklist
        """
        return TokenBlacklist.objects.create(
            token=token,
            usuario=usuario,
            razon=razon
        )
    
    @staticmethod
    def token_en_blacklist(token: str) -> bool:
        """
        Verifica si un token está en el blacklist
        
        Args:
            token (str): Token a verificar
            
        Returns:
            bool: True si está en blacklist, False si no
        """
        return TokenBlacklist.objects.filter(token=token).exists()
    
    @staticmethod
    def limpiar_tokens_expirados() -> int:
        """
        Limpia tokens expirados del blacklist (más de 30 días)
        
        Returns:
            int: Número de tokens eliminados
        """
        fecha_limite = timezone.now() - timezone.timedelta(days=30)
        tokens_expirados = TokenBlacklist.objects.filter(
            fecha_invalidacion__lt=fecha_limite
        )
        count = tokens_expirados.count()
        tokens_expirados.delete()
        return count
    
    @staticmethod
    def obtener_tokens_usuario(usuario_id: str) -> QuerySet[TokenBlacklist]:
        """
        Obtiene todos los tokens invalidados de un usuario
        
        Args:
            usuario_id (str): ID del usuario
            
        Returns:
            QuerySet[TokenBlacklist]: Tokens invalidados del usuario
        """
        return TokenBlacklist.objects.filter(usuario_id=usuario_id)
    
    @staticmethod
    def invalidar_todos_tokens_usuario(usuario: Usuario, razon: str = 'security') -> int:
        """
        Invalida todos los tokens activos de un usuario
        (Esta función requeriría integración con el sistema JWT)
        
        Args:
            usuario (Usuario): Usuario cuyos tokens invalidar
            razon (str): Razón de la invalidación
            
        Returns:
            int: Número de tokens invalidados
        """
        # Aquí se podría implementar la lógica para invalidar todos los tokens
        # activos del usuario, pero requiere integración con el sistema JWT
        pass