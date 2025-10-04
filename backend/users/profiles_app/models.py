"""
Modelos para el microservicio USERS
Sistema Pontificia - Users Service
"""
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Profile(models.Model):
    """
    Modelo Profile para información adicional de usuarios
    Sincronizado con auth_service mediante usuario_id
    """
    
    # Campo principal de referencia al usuario en auth_service
    usuario_id = models.PositiveIntegerField(
        unique=True,
        help_text='ID del usuario en el servicio de autenticación'
    )
    
    # Información de contacto
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Número de teléfono debe tener el formato: +999999999. Máximo 15 dígitos.'
            )
        ],
        help_text='Número de teléfono del usuario'
    )
    
    direccion = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text='Dirección de residencia del usuario'
    )
    
    # Información laboral/académica
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Cargo o posición del usuario'
    )
    
    departamento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Departamento o área de trabajo/estudio'
    )
    
    fecha_ingreso = models.DateField(
        null=True,
        blank=True,
        help_text='Fecha de ingreso a la institución'
    )
    
    # Campos adicionales opcionales
    biografia = models.TextField(
        blank=True,
        null=True,
        max_length=1000,
        help_text='Biografía o descripción personal'
    )
    
    avatar_url = models.URLField(
        blank=True,
        null=True,
        help_text='URL del avatar del usuario'
    )
    
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        help_text='Fecha de nacimiento'
    )
    
    # Configuración de privacidad
    perfil_publico = models.BooleanField(
        default=True,
        help_text='Indica si el perfil es visible públicamente'
    )
    
    mostrar_telefono = models.BooleanField(
        default=False,
        help_text='Mostrar teléfono en el perfil público'
    )
    
    mostrar_correo = models.BooleanField(
        default=True,
        help_text='Mostrar correo en el perfil público'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora de creación del perfil'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text='Fecha y hora de última actualización'
    )
    
    activo = models.BooleanField(
        default=True,
        help_text='Indica si el perfil está activo'
    )
    
    class Meta:
        db_table = 'profiles'
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario_id']),
            models.Index(fields=['departamento']),
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"Perfil Usuario ID: {self.usuario_id}"
    
    @property
    def edad(self):
        """Calcula la edad del usuario si tiene fecha de nacimiento"""
        if self.fecha_nacimiento:
            today = timezone.now().date()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None
    
    @property
    def anos_en_institucion(self):
        """Calcula los años en la institución si tiene fecha de ingreso"""
        if self.fecha_ingreso:
            today = timezone.now().date()
            return today.year - self.fecha_ingreso.year - (
                (today.month, today.day) < (self.fecha_ingreso.month, self.fecha_ingreso.day)
            )
        return None
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar que fecha_nacimiento no sea futura
        if self.fecha_nacimiento and self.fecha_nacimiento > timezone.now().date():
            raise ValidationError({'fecha_nacimiento': 'La fecha de nacimiento no puede ser futura'})
        
        # Validar que fecha_ingreso no sea muy antigua (más de 50 años)
        if self.fecha_ingreso:
            hace_50_anos = timezone.now().date().replace(year=timezone.now().year - 50)
            if self.fecha_ingreso < hace_50_anos:
                raise ValidationError({'fecha_ingreso': 'La fecha de ingreso parece incorrecta'})
    
    def save(self, *args, **kwargs):
        """Override save para validaciones adicionales"""
        self.full_clean()
        super().save(*args, **kwargs)
