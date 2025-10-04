"""
Modelos del microservicio AUTH - Sistema Pontificia
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import re


class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario"""
    
    def create_user(self, correo, dni, password=None, **extra_fields):
        """Crear usuario regular"""
        if not correo:
            raise ValueError('El correo electrónico es requerido')
            raise ValueError('El DNI es requerido')
            
        correo = self.normalize_email(correo)
        user = self.model(correo=correo, dni=dni, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, correo, dni, password=None, **extra_fields):
        """Crear superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', Usuario.ROL_ADMIN)
        extra_fields.setdefault('estado', Usuario.ESTADO_ACTIVO)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(correo, dni, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo Usuario personalizado para el sistema Pontificia
    Maneja autenticación y autorización de usuarios
    """
    
    # Choices para roles
    ROL_ADMIN = 'ADMIN'
    ROL_DOCENTE = 'DOCENTE'
    ROL_RRHH = 'RRHH'
    ROL_CONTABILIDAD = 'CONTABILIDAD'
    ROL_ESTUDIANTE = 'ESTUDIANTE'
    
    ROLES_CHOICES = [
        (ROL_ADMIN, 'Administrador'),
        (ROL_DOCENTE, 'Docente'),
        (ROL_RRHH, 'Recursos Humanos'),
        (ROL_CONTABILIDAD, 'Contabilidad'),
        (ROL_ESTUDIANTE, 'Estudiante'),
    ]
    
    # Choices para estados
    ESTADO_ACTIVO = 'ACTIVO'
    ESTADO_INACTIVO = 'INACTIVO'
    ESTADO_SUSPENDIDO = 'SUSPENDIDO'
    ESTADO_PENDIENTE = 'PENDIENTE'
    
    ESTADOS_CHOICES = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_INACTIVO, 'Inactivo'),
        (ESTADO_SUSPENDIDO, 'Suspendido'),
        (ESTADO_PENDIENTE, 'Pendiente Activación'),
    ]
    
    # Validadores
    dni_validator = RegexValidator(
        regex=r'^\d{6,12}$',
        message='DNI debe contener entre 6 y 12 dígitos'
    )
    
    telefono_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Número de teléfono debe tener el formato: +999999999. Máximo 15 dígitos.'
    )
    
    # Campos principales
    id = models.AutoField(primary_key=True)
    
    dni = models.CharField(
        max_length=12,
        unique=True,
        validators=[dni_validator],
        help_text='Documento de identidad único'
    )
    nombre = models.CharField(
        max_length=100,
        help_text='Nombres del usuario'
    )
    apellido = models.CharField(
        max_length=100,
        help_text='Apellidos del usuario'
    )
    correo = models.EmailField(
        max_length=150,
        unique=True,
        help_text='Correo electrónico único'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[telefono_validator],
        help_text='Número de teléfono'
    )
    
    # Campos de rol y estado
    rol = models.CharField(
        max_length=20,
        choices=ROLES_CHOICES,
        default=ROL_ESTUDIANTE,
        help_text='Rol del usuario en el sistema'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CHOICES,
        default=ESTADO_PENDIENTE,
        help_text='Estado actual del usuario'
    )
    
    
    # Campos de auditoría y control
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora de creación del usuario'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text='Fecha y hora de última actualización'
    )
    ultimo_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora del último inicio de sesión'
    )
    fecha_vencimiento_password = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de vencimiento de la contraseña'
    )
    intentos_login_fallidos = models.PositiveSmallIntegerField(
        default=0,
        help_text='Número de intentos de login fallidos consecutivos'
    )
    fecha_bloqueo = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de bloqueo por intentos fallidos'
    )
    
    # Campos adicionales opcionales
    avatar = models.URLField(
        blank=True,
        null=True,
        help_text='URL del avatar del usuario'
    )
    departamento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Departamento o área de trabajo'
    )
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Cargo o posición'
    )
    
    # Campos para Django Admin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Override inherited fields to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='usuarios',
        related_query_name='usuario',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='usuarios',
        related_query_name='usuario',
    )
    
    
    # Manager personalizado
    objects = UsuarioManager()
    
    # Configuración de autenticación
    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['dni', 'nombre', 'apellido']
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['correo']),
            models.Index(fields=['dni']),
            models.Index(fields=['rol']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.correo})"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar formato del correo (usando el validador de Django que es más flexible)
        from django.core.validators import validate_email
        if self.correo:
            try:
                validate_email(self.correo)
            except ValidationError:
                raise ValidationError({'correo': 'Formato de correo electrónico inválido'})
        
        # Validar DNI
        if self.dni and not self.dni.isdigit():
            raise ValidationError({'dni': 'DNI debe contener solo dígitos'})
        
        # Validar nombres y apellidos
        if self.nombre and len(self.nombre.strip()) < 2:
            raise ValidationError({'nombre': 'El nombre debe tener al menos 2 caracteres'})
        
        if self.apellido and len(self.apellido.strip()) < 2:
            raise ValidationError({'apellido': 'El apellido debe tener al menos 2 caracteres'})
    
    def save(self, *args, **kwargs):
        """Override save para validaciones adicionales"""
        self.clean()
        
        # Normalizar correo
        if self.correo:
            self.correo = self.correo.lower().strip()
        
        # Normalizar nombres
        if self.nombre:
            self.nombre = self.nombre.strip().title()
        if self.apellido:
            self.apellido = self.apellido.strip().title()
        
        # Auto-asignar is_staff para ADMIN
        if self.rol == self.ROL_ADMIN:
            self.is_staff = True
        
        super().save(*args, **kwargs)
    
    @property
    def nombre_completo(self):
        """Retorna nombre completo del usuario"""
        return f"{self.nombre} {self.apellido}".strip()
    
    @property
    def iniciales(self):
        """Retorna iniciales del usuario"""
        nombre_inicial = self.nombre[0] if self.nombre else ''
        apellido_inicial = self.apellido[0] if self.apellido else ''
        return f"{nombre_inicial}{apellido_inicial}".upper()
    
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == self.ROL_ADMIN
    
    def es_docente(self):
        """Verifica si el usuario es docente"""
        return self.rol == self.ROL_DOCENTE
    
    def es_rrhh(self):
        """Verifica si el usuario es de RRHH"""
        return self.rol == self.ROL_RRHH
    
    def es_contabilidad(self):
        """Verifica si el usuario es de contabilidad"""
        return self.rol == self.ROL_CONTABILIDAD
    
    def es_estudiante(self):
        """Verifica si el usuario es estudiante"""
        return self.rol == self.ROL_ESTUDIANTE
    
    def esta_activo(self):
        """Verifica si el usuario está activo"""
        return self.estado == self.ESTADO_ACTIVO and self.is_active
    
    def puede_iniciar_sesion(self):
        """Verifica si el usuario puede iniciar sesión"""
        return (
            self.esta_activo() and 
            self.intentos_login_fallidos < 5 and
            (not self.fecha_bloqueo or 
             timezone.now() > self.fecha_bloqueo + timezone.timedelta(hours=1))
        )
    
    def bloquear_usuario(self):
        """Bloquea el usuario por intentos fallidos"""
        self.fecha_bloqueo = timezone.now()
        self.save(update_fields=['fecha_bloqueo'])
    
    def desbloquear_usuario(self):
        """Desbloquea el usuario"""
        self.intentos_login_fallidos = 0
        self.fecha_bloqueo = None
        self.save(update_fields=['intentos_login_fallidos', 'fecha_bloqueo'])
    
    def incrementar_intentos_fallidos(self):
        """Incrementa contador de intentos fallidos"""
        self.intentos_login_fallidos += 1
        if self.intentos_login_fallidos >= 5:
            self.bloquear_usuario()
        else:
            self.save(update_fields=['intentos_login_fallidos'])
    
    def activar_usuario(self):
        """Activa el usuario"""
        self.estado = self.ESTADO_ACTIVO
        self.is_active = True
        self.save(update_fields=['estado', 'is_active'])
    
    def desactivar_usuario(self):
        """Desactiva el usuario"""
        self.estado = self.ESTADO_INACTIVO
        self.is_active = False
        self.save(update_fields=['estado', 'is_active'])
    

class HistorialLogin(models.Model):
    """
    Modelo para registrar el historial de inicios de sesión
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='historial_logins'
    )
    fecha_login = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    exitoso = models.BooleanField(default=True)
    razon_fallo = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'historial_logins'
        verbose_name = 'Historial de Login'
        verbose_name_plural = 'Historial de Logins'
        ordering = ['-fecha_login']
    
    def __str__(self):
        estado = "Exitoso" if self.exitoso else "Fallido"
        return f"{self.usuario.correo} - {estado} - {self.fecha_login}"


class SesionUsuario(models.Model):
    """
    Modelo para manejar sesiones activas de usuarios
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='sesiones'
    )
    token_id = models.CharField(max_length=255, unique=True)
    refresh_token_id = models.CharField(max_length=255, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'sesiones_usuarios'
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuarios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.usuario.correo} - {self.fecha_creacion}"
    
    def es_valida(self):
        """Verifica si la sesión es válida"""
        return (
            self.activa and 
            timezone.now() < self.fecha_expiracion
        )
    
    def cerrar_sesion(self):
        """Cierra la sesión"""
        self.activa = False
        self.save(update_fields=['activa'])


        return f"Token invalidado - {self.usuario.dni} - {self.fecha_invalidacion}"
