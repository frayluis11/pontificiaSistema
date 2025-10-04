"""
Servicio de Autenticación - Sistema Pontificia
Implementa la lógica de negocio para autenticación JWT
"""
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import Usuario, HistorialLogin, SesionUsuario
from .repository import UsuarioRepository
import logging
import hashlib

logger = logging.getLogger(__name__)


class AuthService:
    """
    Servicio principal para operaciones de autenticación
    Maneja registro, login, logout y refresh de tokens JWT
    """
    
    @staticmethod
    def registrar_usuario(data, ip_address='', user_agent=''):
        """
        Registrar un nuevo usuario en el sistema
        
        Args:
            data (dict): Datos del usuario a registrar
            ip_address (str): Dirección IP del cliente
            user_agent (str): User agent del cliente
            
        Returns:
            dict: Usuario creado y tokens JWT
        """
        try:
            # Validar datos requeridos
            campos_requeridos = ['correo', 'dni', 'nombre', 'apellido', 'password']
            for campo in campos_requeridos:
                if not data.get(campo):
                    raise ValidationError(f"El campo {campo} es requerido")
            
            # Validar fortaleza de la contraseña
            password = data.get('password')
            if len(password) < 8:
                raise ValidationError("La contraseña debe tener al menos 8 caracteres")
            
            # Crear usuario usando el repositorio
            usuario = UsuarioRepository.crear_usuario(data)
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(usuario)
            access_token = refresh.access_token
            
            # Registrar la sesión
            UsuarioRepository.crear_sesion(
                usuario=usuario,
                token_id=str(access_token.get('jti', '')),
                refresh_token_id=str(refresh.get('jti', '')),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Registrar en historial
            UsuarioRepository.registrar_login(
                usuario=usuario,
                ip_address=ip_address,
                user_agent=user_agent,
                exitoso=True
            )
            
            logger.info(f"Usuario registrado exitosamente: {usuario.correo}")
            
            return {
                'usuario': {
                    'id': usuario.id,
                    'correo': usuario.correo,
                    'dni': usuario.dni,
                    'nombre': usuario.nombre,
                    'apellido': usuario.apellido,
                    'rol': usuario.rol,
                    'estado': usuario.estado,
                    'nombre_completo': usuario.nombre_completo
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh)
                },
                'message': 'Usuario registrado exitosamente'
            }
            
        except ValidationError as e:
            logger.warning(f"Error de validación en registro: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error inesperado en registro: {str(e)}")
            raise ValidationError(f"Error al registrar usuario: {str(e)}")
    
    @staticmethod
    def login(correo, password, ip_address='', user_agent=''):
        """
        Autenticar usuario y generar tokens JWT
        
        Args:
            correo (str): Correo electrónico del usuario
            password (str): Contraseña del usuario
            ip_address (str): Dirección IP del cliente
            user_agent (str): User agent del cliente
            
        Returns:
            dict: Usuario autenticado y tokens JWT
        """
        try:
            # Obtener usuario por correo
            usuario = UsuarioRepository.obtener_por_correo(correo)
            
            if not usuario:
                # Registrar intento fallido
                logger.warning(f"Intento de login con correo inexistente: {correo}")
                raise ValidationError("Credenciales inválidas")
            
            # Verificar si el usuario puede iniciar sesión
            if not usuario.puede_iniciar_sesion():
                razon = "Usuario bloqueado por intentos fallidos" if usuario.fecha_bloqueo else "Usuario inactivo"
                
                UsuarioRepository.registrar_login(
                    usuario=usuario,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    exitoso=False,
                    razon_fallo=razon
                )
                
                raise ValidationError(razon)
            
            # Verificar contraseña
            if not usuario.check_password(password):
                # Registrar intento fallido
                UsuarioRepository.registrar_login(
                    usuario=usuario,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    exitoso=False,
                    razon_fallo="Contraseña incorrecta"
                )
                
                logger.warning(f"Contraseña incorrecta para usuario: {correo}")
                raise ValidationError("Credenciales inválidas")
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(usuario)
            access_token = refresh.access_token
            
            # Crear sesión
            UsuarioRepository.crear_sesion(
                usuario=usuario,
                token_id=str(access_token.get('jti', '')),
                refresh_token_id=str(refresh.get('jti', '')),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Registrar login exitoso
            UsuarioRepository.registrar_login(
                usuario=usuario,
                ip_address=ip_address,
                user_agent=user_agent,
                exitoso=True
            )
            
            logger.info(f"Login exitoso para usuario: {correo}")
            
            return {
                'usuario': {
                    'id': usuario.id,
                    'correo': usuario.correo,
                    'dni': usuario.dni,
                    'nombre': usuario.nombre,
                    'apellido': usuario.apellido,
                    'rol': usuario.rol,
                    'estado': usuario.estado,
                    'nombre_completo': usuario.nombre_completo,
                    'ultimo_login': usuario.ultimo_login.isoformat() if usuario.ultimo_login else None
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh)
                },
                'message': 'Login exitoso'
            }
            
        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error inesperado en login: {str(e)}")
            raise ValidationError(f"Error en el proceso de autenticación: {str(e)}")
    
    @staticmethod
    def logout(refresh_token, usuario_id=None):
        """
        Cerrar sesión e invalidar tokens
        
        Args:
            refresh_token (str): Token de refresh a invalidar
            usuario_id (int): ID del usuario (opcional)
            
        Returns:
            dict: Mensaje de confirmación
        """
        try:
            # Validar y obtener el refresh token
            token = RefreshToken(refresh_token)
            token_id = str(token.get('jti', ''))
            
            # Obtener usuario del token si no se proporciona
            if not usuario_id:
                usuario_id = token.get('user_id')
            
            # Cerrar sesiones activas del usuario
            SesionUsuario.objects.filter(
                usuario_id=usuario_id,
                refresh_token_id=token_id
            ).update(activa=False)
            
            # Blacklist del token
            token.blacklist()
            
            logger.info(f"Logout exitoso para usuario ID: {usuario_id}")
            
            return {
                'message': 'Sesión cerrada exitosamente'
            }
            
        except TokenError as e:
            logger.warning(f"Error de token en logout: {str(e)}")
            raise ValidationError("Token inválido")
        except Exception as e:
            logger.error(f"Error inesperado en logout: {str(e)}")
            raise ValidationError(f"Error al cerrar sesión: {str(e)}")
    
    @staticmethod
    def refresh_token(refresh_token):
        """
        Renovar access token usando refresh token
        
        Args:
            refresh_token (str): Token de refresh
            
        Returns:
            dict: Nuevo access token
        """
        try:
            # Validar refresh token
            refresh = RefreshToken(refresh_token)
            
            # Verificar que el token no esté en blacklist
            if not refresh.check_blacklist():
                raise ValidationError("Token de refresh inválido")
            
            # Obtener usuario
            usuario_id = refresh.get('user_id')
            usuario = UsuarioRepository.obtener_por_id(usuario_id)
            
            if not usuario:
                raise ValidationError("Usuario no encontrado")
            
            # Verificar que el usuario pueda usar el token
            if not usuario.puede_iniciar_sesion():
                raise ValidationError("Usuario no autorizado")
            
            # Generar nuevo access token
            new_access_token = refresh.access_token
            
            # Actualizar sesión existente
            SesionUsuario.objects.filter(
                usuario=usuario,
                refresh_token_id=str(refresh.get('jti', ''))
            ).update(
                token_id=str(new_access_token.get('jti', '')),
                fecha_expiracion=timezone.now() + timezone.timedelta(hours=1)
            )
            
            logger.info(f"Token renovado para usuario: {usuario.correo}")
            
            return {
                'access': str(new_access_token),
                'message': 'Token renovado exitosamente'
            }
            
        except TokenError as e:
            logger.warning(f"Error de token en refresh: {str(e)}")
            raise ValidationError("Token de refresh inválido")
        except Exception as e:
            logger.error(f"Error inesperado en refresh: {str(e)}")
            raise ValidationError(f"Error al renovar token: {str(e)}")
    
    @staticmethod
    def verificar_token(access_token):
        """
        Verificar validez de un access token
        
        Args:
            access_token (str): Token de acceso a verificar
            
        Returns:
            dict: Información del token y usuario
        """
        try:
            # Verificar token
            token = UntypedToken(access_token)
            usuario_id = token.get('user_id')
            
            # Obtener usuario
            usuario = UsuarioRepository.obtener_por_id(usuario_id)
            
            if not usuario:
                raise ValidationError("Usuario no encontrado")
            
            # Verificar que el usuario esté activo
            if not usuario.puede_iniciar_sesion():
                raise ValidationError("Usuario no autorizado")
            
            return {
                'valid': True,
                'usuario': {
                    'id': usuario.id,
                    'correo': usuario.correo,
                    'rol': usuario.rol,
                    'estado': usuario.estado
                },
                'token_info': {
                    'exp': token.get('exp'),
                    'iat': token.get('iat'),
                    'jti': token.get('jti')
                }
            }
            
        except InvalidToken as e:
            logger.warning(f"Token inválido: {str(e)}")
            return {
                'valid': False,
                'error': 'Token inválido'
            }
        except Exception as e:
            logger.error(f"Error verificando token: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def cambiar_password(usuario_id, password_actual, password_nueva):
        """
        Cambiar contraseña del usuario
        
        Args:
            usuario_id (int): ID del usuario
            password_actual (str): Contraseña actual
            password_nueva (str): Nueva contraseña
            
        Returns:
            dict: Mensaje de confirmación
        """
        try:
            # Validar nueva contraseña
            if len(password_nueva) < 8:
                raise ValidationError("La nueva contraseña debe tener al menos 8 caracteres")
            
            # Cambiar contraseña usando repositorio
            usuario = UsuarioRepository.cambiar_password(
                usuario_id, password_actual, password_nueva
            )
            
            # Cerrar todas las sesiones del usuario (forzar re-login)
            UsuarioRepository.cerrar_sesiones_usuario(usuario_id)
            
            logger.info(f"Contraseña cambiada para usuario: {usuario.correo}")
            
            return {
                'message': 'Contraseña cambiada exitosamente'
            }
            
        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error cambiando contraseña: {str(e)}")
            raise ValidationError(f"Error al cambiar contraseña: {str(e)}")
    
    @staticmethod
    def cerrar_todas_las_sesiones(usuario_id):
        """
        Cerrar todas las sesiones activas de un usuario
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            dict: Mensaje de confirmación
        """
        try:
            UsuarioRepository.cerrar_sesiones_usuario(usuario_id)
            
            logger.info(f"Todas las sesiones cerradas para usuario ID: {usuario_id}")
            
            return {
                'message': 'Todas las sesiones han sido cerradas'
            }
            
        except Exception as e:
            logger.error(f"Error cerrando sesiones: {str(e)}")
            raise ValidationError(f"Error al cerrar sesiones: {str(e)}")
    
    @staticmethod
    def obtener_perfil_usuario(usuario_id):
        """
        Obtener perfil completo del usuario
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            dict: Información del perfil del usuario
        """
        try:
            usuario = UsuarioRepository.obtener_por_id(usuario_id)
            
            if not usuario:
                raise ValidationError("Usuario no encontrado")
            
            return {
                'id': usuario.id,
                'dni': usuario.dni,
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'correo': usuario.correo,
                'telefono': usuario.telefono,
                'rol': usuario.rol,
                'estado': usuario.estado,
                'departamento': usuario.departamento,
                'cargo': usuario.cargo,
                'avatar': usuario.avatar,
                'fecha_creacion': usuario.fecha_creacion.isoformat(),
                'ultimo_login': usuario.ultimo_login.isoformat() if usuario.ultimo_login else None,
                'nombre_completo': usuario.nombre_completo,
                'iniciales': usuario.iniciales
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo perfil: {str(e)}")
            raise ValidationError(f"Error al obtener perfil: {str(e)}")
