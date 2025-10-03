"""
Serializers para la API REST del microservicio de autenticación
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Usuario
from .factory import UsuarioFactory


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Usuario
    """
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'dni', 'nombre', 'apellido', 'nombre_completo',
            'correo', 'rol', 'estado', 'fecha_creacion',
            'fecha_modificacion', 'fecha_ultimo_acceso',
            'is_active'
        ]
        read_only_fields = [
            'id', 'fecha_creacion', 'fecha_modificacion',
            'fecha_ultimo_acceso'
        ]
    
    def get_nombre_completo(self, obj):
        return obj.get_full_name()


class RegistrarUsuarioSerializer(serializers.Serializer):
    """
    Serializer para el registro de usuarios
    """
    dni = serializers.CharField(
        max_length=10,
        min_length=7,
        help_text='Documento Nacional de Identidad (7-10 dígitos)'
    )
    nombre = serializers.CharField(
        max_length=100,
        help_text='Nombre(s) del usuario'
    )
    apellido = serializers.CharField(
        max_length=100,
        help_text='Apellido(s) del usuario'
    )
    correo = serializers.EmailField(
        help_text='Correo electrónico único'
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña del usuario'
    )
    password_confirmacion = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmación de contraseña'
    )
    rol = serializers.ChoiceField(
        choices=Usuario.ROLES_CHOICES,
        default=Usuario.ROL_ESTUDIANTE,
        help_text='Rol del usuario en el sistema'
    )
    
    def validate_dni(self, value):
        """Validar DNI"""
        if not value.isdigit():
            raise serializers.ValidationError("El DNI debe contener solo números")
        
        if Usuario.objects.filter(dni=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este DNI")
        
        return value
    
    def validate_correo(self, value):
        """Validar correo"""
        if Usuario.objects.filter(correo=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo")
        
        return value
    
    def validate_password(self, value):
        """Validar contraseña"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        if attrs['password'] != attrs['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Crear usuario"""
        validated_data.pop('password_confirmacion')
        return UsuarioFactory.crear_usuario_por_rol(
            rol=validated_data.pop('rol', Usuario.ROL_ESTUDIANTE),
            **validated_data
        )


class LoginSerializer(serializers.Serializer):
    """
    Serializer para el login de usuarios
    """
    dni = serializers.CharField(
        max_length=10,
        help_text='Documento Nacional de Identidad'
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña del usuario'
    )
    
    def validate_dni(self, value):
        """Validar que el DNI solo contenga números"""
        if not value.isdigit():
            raise serializers.ValidationError("El DNI debe contener solo números")
        return value


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de tokens JWT
    """
    access_token = serializers.CharField(help_text='Token de acceso JWT')
    refresh_token = serializers.CharField(help_text='Token de refresh JWT')
    token_type = serializers.CharField(default='Bearer', help_text='Tipo de token')
    expires_in = serializers.IntegerField(help_text='Tiempo de expiración en segundos')
    usuario = UsuarioSerializer(help_text='Datos del usuario autenticado')


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para el logout
    """
    refresh_token = serializers.CharField(
        help_text='Token de refresh a invalidar'
    )


class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer para renovar tokens
    """
    refresh_token = serializers.CharField(
        help_text='Token de refresh actual'
    )


class RefreshTokenResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de renovación de tokens
    """
    access_token = serializers.CharField(help_text='Nuevo token de acceso JWT')
    refresh_token = serializers.CharField(help_text='Nuevo token de refresh JWT')
    token_type = serializers.CharField(default='Bearer', help_text='Tipo de token')


class CambiarPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña
    """
    password_actual = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña actual'
    )
    password_nueva = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Nueva contraseña'
    )
    password_confirmacion = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmación de nueva contraseña'
    )
    
    def validate_password_nueva(self, value):
        """Validar nueva contraseña"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Validar que las contraseñas nuevas coincidan"""
        if attrs['password_nueva'] != attrs['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden'
            })
        
        return attrs


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del usuario (más detallado)
    """
    nombre_completo = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'dni', 'nombre', 'apellido', 'nombre_completo',
            'correo', 'rol', 'estado', 'fecha_creacion',
            'fecha_modificacion', 'fecha_ultimo_acceso',
            'is_active', 'is_staff', 'permisos'
        ]
        read_only_fields = [
            'id', 'dni', 'rol', 'estado', 'fecha_creacion',
            'fecha_modificacion', 'fecha_ultimo_acceso',
            'is_active', 'is_staff'
        ]
    
    def get_nombre_completo(self, obj):
        return obj.get_full_name()
    
    def get_permisos(self, obj):
        return {
            'is_admin': obj.is_admin,
            'is_docente': obj.is_docente,
            'is_rrhh': obj.is_rrhh,
            'is_contabilidad': obj.is_contabilidad,
            'is_estudiante': obj.is_estudiante,
        }


class ActualizarPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar el perfil del usuario
    """
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo']
    
    def validate_correo(self, value):
        """Validar que el correo no esté en uso por otro usuario"""
        if self.instance and self.instance.correo == value:
            return value
        
        if Usuario.objects.filter(correo=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo")
        
        return value


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer para respuestas de error
    """
    error = serializers.CharField(help_text='Mensaje de error')
    detail = serializers.CharField(required=False, help_text='Detalle del error')
    codigo = serializers.CharField(required=False, help_text='Código de error')


class MensajeResponseSerializer(serializers.Serializer):
    """
    Serializer para respuestas de mensaje
    """
    mensaje = serializers.CharField(help_text='Mensaje de respuesta')
    exito = serializers.BooleanField(default=True, help_text='Indica si la operación fue exitosa')


class EstadisticasUsuariosSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de usuarios
    """
    total_usuarios = serializers.IntegerField(help_text='Total de usuarios')
    usuarios_activos = serializers.IntegerField(help_text='Usuarios activos')
    usuarios_inactivos = serializers.IntegerField(help_text='Usuarios inactivos')
    total_admin = serializers.IntegerField(help_text='Total de administradores')
    total_docente = serializers.IntegerField(help_text='Total de docentes')
    total_rrhh = serializers.IntegerField(help_text='Total de RRHH')
    total_contabilidad = serializers.IntegerField(help_text='Total de contabilidad')
    total_estudiante = serializers.IntegerField(help_text='Total de estudiantes')


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer para respuesta de tokens JWT
    """
    access_token = serializers.CharField(help_text='Token de acceso JWT')
    refresh_token = serializers.CharField(help_text='Token de renovación JWT')
    token_type = serializers.CharField(default='Bearer', help_text='Tipo de token')
    expires_in = serializers.IntegerField(help_text='Tiempo de expiración en segundos')
    usuario = UsuarioSerializer(help_text='Datos del usuario autenticado')


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para logout
    """
    refresh_token = serializers.CharField(help_text='Token de renovación a invalidar')


class RefreshTokenResponseSerializer(serializers.Serializer):
    """
    Serializer para respuesta de renovación de token
    """
    access_token = serializers.CharField(help_text='Nuevo token de acceso JWT')
    token_type = serializers.CharField(default='Bearer', help_text='Tipo de token')
    expires_in = serializers.IntegerField(help_text='Tiempo de expiración en segundos')


class CambiarPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña
    """
    password_actual = serializers.CharField(
        write_only=True,
        help_text='Contraseña actual del usuario'
    )
    password_nueva = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Nueva contraseña (mínimo 8 caracteres)'
    )
    password_nueva_confirmacion = serializers.CharField(
        write_only=True,
        help_text='Confirmación de la nueva contraseña'
    )
    
    def validate_password_nueva(self, value):
        """Validar nueva contraseña con las políticas de Django"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validar que las contraseñas nuevas coincidan"""
        if attrs.get('password_nueva') != attrs.get('password_nueva_confirmacion'):
            raise serializers.ValidationError({
                'password_nueva_confirmacion': 'Las contraseñas no coinciden'
            })
        
        # Remover confirmación ya que no se necesita guardar
        attrs.pop('password_nueva_confirmacion', None)
        return attrs


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del usuario
    """
    nombre_completo = serializers.SerializerMethodField()
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'dni', 'nombre', 'apellido', 'nombre_completo',
            'correo', 'rol', 'rol_display', 'estado',
            'fecha_creacion', 'fecha_ultimo_acceso', 'is_active'
        ]
        read_only_fields = ['id', 'dni', 'rol', 'fecha_creacion', 'fecha_ultimo_acceso']
    
    def get_nombre_completo(self, obj):
        return obj.get_full_name()