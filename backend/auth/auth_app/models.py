"""
Modelos para el microservicio de autenticación
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario
    """
    
    def create_user(self, dni, correo, password=None, **extra_fields):
        """
        Crear y guardar un usuario regular
        """
        if not dni:
            raise ValueError('El DNI es obligatorio')
        if not correo:
            raise ValueError('El correo electrónico es obligatorio')
        
        correo = self.normalize_email(correo)
        user = self.model(dni=dni, correo=correo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, dni, correo, password=None, **extra_fields):
        """
        Crear y guardar un superusuario
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', Usuario.ROL_ADMIN)
        extra_fields.setdefault('estado', Usuario.ESTADO_ACTIVO)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(dni, correo, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo personalizado de Usuario para el sistema de autenticación
    """
    
    # Opciones de rol
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
    
    # Opciones de estado
    ESTADO_ACTIVO = 'ACTIVO'
    ESTADO_INACTIVO = 'INACTIVO'
    ESTADO_SUSPENDIDO = 'SUSPENDIDO'
    ESTADO_BLOQUEADO = 'BLOQUEADO'
    
    ESTADOS_CHOICES = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_INACTIVO, 'Inactivo'),
        (ESTADO_SUSPENDIDO, 'Suspendido'),
        (ESTADO_BLOQUEADO, 'Bloqueado'),
    ]
    
    # Validador para DNI (solo números, 7-10 dígitos)
    dni_validator = RegexValidator(
        regex=r'^\d{7,10}$',
        message='El DNI debe contener entre 7 y 10 dígitos numéricos'
    )
    
    # Campos del modelo
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Identificador único del usuario'
    )
    
    dni = models.CharField(
        max_length=10,
        unique=True,
        validators=[dni_validator],
        help_text='Documento Nacional de Identidad'
    )
    
    nombre = models.CharField(
        max_length=100,
        help_text='Nombre(s) del usuario'
    )
    
    apellido = models.CharField(
        max_length=100,
        help_text='Apellido(s) del usuario'
    )
    
    correo = models.EmailField(
        unique=True,
        help_text='Correo electrónico único del usuario'
    )
    
    rol = models.CharField(
        max_length=15,
        choices=ROLES_CHOICES,
        default=ROL_ESTUDIANTE,
        help_text='Rol del usuario en el sistema'
    )
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS_CHOICES,
        default=ESTADO_ACTIVO,
        help_text='Estado actual del usuario'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        help_text='Fecha y hora de creación del usuario'
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        help_text='Fecha y hora de última modificación'
    )
    
    fecha_ultimo_acceso = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora del último acceso al sistema'
    )
    
    # Campos requeridos por Django
    is_active = models.BooleanField(
        default=True,
        help_text='Indica si el usuario está activo en el sistema'
    )
    
    is_staff = models.BooleanField(
        default=False,
        help_text='Indica si el usuario puede acceder al panel de administración'
    )
    
    # Configuración del manager
    objects = UsuarioManager()
    
    # Configuración de autenticación
    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['correo', 'nombre', 'apellido']
    
    class Meta:
        db_table = 'auth_usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['dni']),
            models.Index(fields=['correo']),
            models.Index(fields=['rol']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.dni})"
    
    def get_full_name(self):
        """
        Retorna el nombre completo del usuario
        """
        return f"{self.nombre} {self.apellido}".strip()
    
    def get_short_name(self):
        """
        Retorna el nombre corto del usuario
        """
        return self.nombre
    
    @property
    def is_admin(self):
        """
        Verifica si el usuario es administrador
        """
        return self.rol == self.ROL_ADMIN
    
    @property
    def is_docente(self):
        """
        Verifica si el usuario es docente
        """
        return self.rol == self.ROL_DOCENTE
    
    @property
    def is_rrhh(self):
        """
        Verifica si el usuario es de recursos humanos
        """
        return self.rol == self.ROL_RRHH
    
    @property
    def is_contabilidad(self):
        """
        Verifica si el usuario es de contabilidad
        """
        return self.rol == self.ROL_CONTABILIDAD
    
    @property
    def is_estudiante(self):
        """
        Verifica si el usuario es estudiante
        """
        return self.rol == self.ROL_ESTUDIANTE
    
    @property
    def estado_activo(self):
        """
        Verifica si el usuario está en estado activo
        """
        return self.estado == self.ESTADO_ACTIVO
    
    def activar(self):
        """
        Activa el usuario
        """
        self.estado = self.ESTADO_ACTIVO
        self.is_active = True
        self.save(update_fields=['estado', 'is_active', 'fecha_modificacion'])
    
    def desactivar(self):
        """
        Desactiva el usuario
        """
        self.estado = self.ESTADO_INACTIVO
        self.is_active = False
        self.save(update_fields=['estado', 'is_active', 'fecha_modificacion'])
    
    def suspender(self):
        """
        Suspende el usuario
        """
        self.estado = self.ESTADO_SUSPENDIDO
        self.is_active = False
        self.save(update_fields=['estado', 'is_active', 'fecha_modificacion'])
    
    def bloquear(self):
        """
        Bloquea el usuario
        """
        self.estado = self.ESTADO_BLOQUEADO
        self.is_active = False
        self.save(update_fields=['estado', 'is_active', 'fecha_modificacion'])
    
    def actualizar_ultimo_acceso(self):
        """
        Actualiza la fecha del último acceso
        """
        self.fecha_ultimo_acceso = timezone.now()
        self.save(update_fields=['fecha_ultimo_acceso'])


class TokenBlacklist(models.Model):
    """
    Modelo para mantener un blacklist de tokens JWT
    """
    
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text='Token JWT que ha sido invalidado (hash)'
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_invalidados',
        help_text='Usuario al que pertenecía el token'
    )
    
    fecha_invalidacion = models.DateTimeField(
        default=timezone.now,
        help_text='Fecha y hora de invalidación del token'
    )
    
    razon = models.CharField(
        max_length=100,
        default='logout',
        help_text='Razón de la invalidación (logout, cambio_password, etc.)'
    )
    
    class Meta:
        db_table = 'auth_token_blacklist'
        verbose_name = 'Token Invalidado'
        verbose_name_plural = 'Tokens Invalidados'
        ordering = ['-fecha_invalidacion']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['usuario']),
            models.Index(fields=['fecha_invalidacion']),
        ]
    
    def __str__(self):
        return f"Token invalidado - {self.usuario.dni} - {self.fecha_invalidacion}"
