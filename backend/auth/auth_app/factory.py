"""
Factory para la creación de usuarios
Implementa el patrón Factory para crear instancias de Usuario
"""
from typing import Dict, Any, Optional
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Usuario
from .repository import UsuarioRepository
import secrets
import string


class UsuarioFactory:
    """
    Factory para crear diferentes tipos de usuarios
    """
    
    @staticmethod
    def crear_usuario(**kwargs) -> Usuario:
        """
        Crea un usuario con los datos proporcionados
        
        Args:
            **kwargs: Datos del usuario
            
        Returns:
            Usuario: Instancia del usuario creado
            
        Raises:
            ValidationError: Si los datos son inválidos
        """
        # Datos requeridos
        campos_requeridos = ['dni', 'nombre', 'apellido', 'correo', 'password']
        for campo in campos_requeridos:
            if campo not in kwargs or not kwargs[campo]:
                raise ValidationError(f"El campo {campo} es requerido")
        
        # Validar contraseña
        validate_password(kwargs['password'])
        
        # Crear usuario
        return UsuarioRepository.crear_usuario(kwargs)
    
    @staticmethod
    def crear_admin(dni: str, nombre: str, apellido: str, correo: str, password: str) -> Usuario:
        """
        Crea un usuario administrador
        
        Args:
            dni (str): DNI del administrador
            nombre (str): Nombre del administrador
            apellido (str): Apellido del administrador
            correo (str): Correo del administrador
            password (str): Contraseña del administrador
            
        Returns:
            Usuario: Administrador creado
        """
        return UsuarioFactory.crear_usuario(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            password=password,
            rol=Usuario.ROL_ADMIN,
            estado=Usuario.ESTADO_ACTIVO,
            is_staff=True,
            is_superuser=True
        )
    
    @staticmethod
    def crear_docente(dni: str, nombre: str, apellido: str, correo: str, password: str) -> Usuario:
        """
        Crea un usuario docente
        
        Args:
            dni (str): DNI del docente
            nombre (str): Nombre del docente
            apellido (str): Apellido del docente
            correo (str): Correo del docente
            password (str): Contraseña del docente
            
        Returns:
            Usuario: Docente creado
        """
        return UsuarioFactory.crear_usuario(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            password=password,
            rol=Usuario.ROL_DOCENTE,
            estado=Usuario.ESTADO_ACTIVO,
            is_staff=True
        )
    
    @staticmethod
    def crear_rrhh(dni: str, nombre: str, apellido: str, correo: str, password: str) -> Usuario:
        """
        Crea un usuario de recursos humanos
        
        Args:
            dni (str): DNI del usuario RRHH
            nombre (str): Nombre del usuario RRHH
            apellido (str): Apellido del usuario RRHH
            correo (str): Correo del usuario RRHH
            password (str): Contraseña del usuario RRHH
            
        Returns:
            Usuario: Usuario RRHH creado
        """
        return UsuarioFactory.crear_usuario(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            password=password,
            rol=Usuario.ROL_RRHH,
            estado=Usuario.ESTADO_ACTIVO,
            is_staff=True
        )
    
    @staticmethod
    def crear_contabilidad(dni: str, nombre: str, apellido: str, correo: str, password: str) -> Usuario:
        """
        Crea un usuario de contabilidad
        
        Args:
            dni (str): DNI del usuario de contabilidad
            nombre (str): Nombre del usuario de contabilidad
            apellido (str): Apellido del usuario de contabilidad
            correo (str): Correo del usuario de contabilidad
            password (str): Contraseña del usuario de contabilidad
            
        Returns:
            Usuario: Usuario de contabilidad creado
        """
        return UsuarioFactory.crear_usuario(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            password=password,
            rol=Usuario.ROL_CONTABILIDAD,
            estado=Usuario.ESTADO_ACTIVO,
            is_staff=True
        )
    
    @staticmethod
    def crear_estudiante(dni: str, nombre: str, apellido: str, correo: str, password: str) -> Usuario:
        """
        Crea un usuario estudiante
        
        Args:
            dni (str): DNI del estudiante
            nombre (str): Nombre del estudiante
            apellido (str): Apellido del estudiante
            correo (str): Correo del estudiante
            password (str): Contraseña del estudiante
            
        Returns:
            Usuario: Estudiante creado
        """
        return UsuarioFactory.crear_usuario(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            password=password,
            rol=Usuario.ROL_ESTUDIANTE,
            estado=Usuario.ESTADO_ACTIVO,
            is_staff=False
        )
    
    @staticmethod
    def crear_usuario_por_rol(rol: str, dni: str, nombre: str, apellido: str, correo: str, password: str) -> Usuario:
        """
        Crea un usuario según el rol especificado
        
        Args:
            rol (str): Rol del usuario
            dni (str): DNI del usuario
            nombre (str): Nombre del usuario
            apellido (str): Apellido del usuario
            correo (str): Correo del usuario
            password (str): Contraseña del usuario
            
        Returns:
            Usuario: Usuario creado
            
        Raises:
            ValueError: Si el rol no es válido
        """
        metodos_rol = {
            Usuario.ROL_ADMIN: UsuarioFactory.crear_admin,
            Usuario.ROL_DOCENTE: UsuarioFactory.crear_docente,
            Usuario.ROL_RRHH: UsuarioFactory.crear_rrhh,
            Usuario.ROL_CONTABILIDAD: UsuarioFactory.crear_contabilidad,
            Usuario.ROL_ESTUDIANTE: UsuarioFactory.crear_estudiante,
        }
        
        if rol not in metodos_rol:
            raise ValueError(f"Rol inválido: {rol}")
        
        return metodos_rol[rol](dni, nombre, apellido, correo, password)
    
    @staticmethod
    def generar_password_temporal() -> str:
        """
        Genera una contraseña temporal segura
        
        Returns:
            str: Contraseña temporal
        """
        # Generar contraseña de 12 caracteres con letras, números y símbolos
        caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(caracteres) for _ in range(12))
        
        # Asegurar que tenga al menos un número, una mayúscula, una minúscula y un símbolo
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        if not any(c in "!@#$%^&*" for c in password):
            password = password[:-1] + secrets.choice("!@#$%^&*")
        
        return password
    
    @staticmethod
    def crear_usuarios_masivos(usuarios_data: list) -> list:
        """
        Crea múltiples usuarios de forma masiva
        
        Args:
            usuarios_data (list): Lista de diccionarios con datos de usuarios
            
        Returns:
            list: Lista de tuplas (usuario_creado, error) donde error es None si fue exitoso
        """
        resultados = []
        
        for datos in usuarios_data:
            try:
                usuario = UsuarioFactory.crear_usuario(**datos)
                resultados.append((usuario, None))
            except Exception as e:
                resultados.append((None, str(e)))
        
        return resultados
    
    @staticmethod
    def validar_datos_usuario(datos: Dict[str, Any]) -> Dict[str, list]:
        """
        Valida los datos de un usuario antes de crearlo
        
        Args:
            datos (Dict): Datos del usuario a validar
            
        Returns:
            Dict: Diccionario con errores encontrados por campo
        """
        errores = {}
        
        # Validar DNI
        dni = datos.get('dni', '')
        if not dni:
            errores['dni'] = ['DNI es requerido']
        elif len(dni) < 7 or len(dni) > 10 or not dni.isdigit():
            errores['dni'] = ['DNI debe tener entre 7 y 10 dígitos numéricos']
        elif UsuarioRepository.existe_dni(dni):
            errores['dni'] = ['Ya existe un usuario con este DNI']
        
        # Validar nombre
        nombre = datos.get('nombre', '')
        if not nombre:
            errores['nombre'] = ['Nombre es requerido']
        elif len(nombre) > 100:
            errores['nombre'] = ['Nombre no puede exceder 100 caracteres']
        
        # Validar apellido
        apellido = datos.get('apellido', '')
        if not apellido:
            errores['apellido'] = ['Apellido es requerido']
        elif len(apellido) > 100:
            errores['apellido'] = ['Apellido no puede exceder 100 caracteres']
        
        # Validar correo
        correo = datos.get('correo', '')
        if not correo:
            errores['correo'] = ['Correo es requerido']
        elif UsuarioRepository.existe_correo(correo):
            errores['correo'] = ['Ya existe un usuario con este correo']
        
        # Validar contraseña
        password = datos.get('password', '')
        if not password:
            errores['password'] = ['Contraseña es requerida']
        else:
            try:
                validate_password(password)
            except ValidationError as e:
                errores['password'] = e.messages
        
        # Validar rol
        rol = datos.get('rol', '')
        if rol and rol not in dict(Usuario.ROLES_CHOICES):
            errores['rol'] = ['Rol inválido']
        
        # Validar estado
        estado = datos.get('estado', '')
        if estado and estado not in dict(Usuario.ESTADOS_CHOICES):
            errores['estado'] = ['Estado inválido']
        
        return errores