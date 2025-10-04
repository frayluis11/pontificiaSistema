"""
Serializadores para la aplicación de perfiles
Sistema Pontificia - Users Service
"""
from rest_framework import serializers
from .models import Profile
from datetime import date


class ProfileCreateSerializer(serializers.Serializer):
    """
    Serializer para crear perfiles
    """
    usuario_id = serializers.IntegerField(min_value=1)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=200, required=False, allow_blank=True)
    cargo = serializers.CharField(max_length=100, required=False, allow_blank=True)
    departamento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    fecha_ingreso = serializers.DateField(required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    biografia = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True)
    perfil_publico = serializers.BooleanField(default=True)
    mostrar_telefono = serializers.BooleanField(default=False)
    mostrar_correo = serializers.BooleanField(default=True)
    
    def validate_fecha_nacimiento(self, value):
        """Validar que la fecha de nacimiento sea coherente"""
        if value and value >= date.today():
            raise serializers.ValidationError("La fecha de nacimiento debe ser anterior a hoy")
        if value and (date.today() - value).days < 18 * 365:
            raise serializers.ValidationError("La edad debe ser mayor a 18 años")
        return value
    
    def validate_fecha_ingreso(self, value):
        """Validar que la fecha de ingreso sea coherente"""
        if value and value > date.today():
            raise serializers.ValidationError("La fecha de ingreso no puede ser futura")
        return value


class ProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer para actualizar perfiles
    """
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=200, required=False, allow_blank=True)
    cargo = serializers.CharField(max_length=100, required=False, allow_blank=True)
    departamento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    fecha_ingreso = serializers.DateField(required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    biografia = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True)
    perfil_publico = serializers.BooleanField(required=False)
    mostrar_telefono = serializers.BooleanField(required=False)
    mostrar_correo = serializers.BooleanField(required=False)
    
    def validate_fecha_nacimiento(self, value):
        """Validar que la fecha de nacimiento sea coherente"""
        if value and value >= date.today():
            raise serializers.ValidationError("La fecha de nacimiento debe ser anterior a hoy")
        if value and (date.today() - value).days < 18 * 365:
            raise serializers.ValidationError("La edad debe ser mayor a 18 años")
        return value
    
    def validate_fecha_ingreso(self, value):
        """Validar que la fecha de ingreso sea coherente"""
        if value and value > date.today():
            raise serializers.ValidationError("La fecha de ingreso no puede ser futura")
        return value


class ProfileReadSerializer(serializers.Serializer):
    """
    Serializer para leer perfiles (respuesta)
    """
    id = serializers.IntegerField(read_only=True)
    usuario_id = serializers.IntegerField(read_only=True)
    telefono = serializers.CharField(read_only=True)
    direccion = serializers.CharField(read_only=True)
    cargo = serializers.CharField(read_only=True)
    departamento = serializers.CharField(read_only=True)
    fecha_ingreso = serializers.DateField(read_only=True)
    fecha_nacimiento = serializers.DateField(read_only=True)
    biografia = serializers.CharField(read_only=True)
    avatar_url = serializers.URLField(read_only=True)
    perfil_publico = serializers.BooleanField(read_only=True)
    mostrar_telefono = serializers.BooleanField(read_only=True)
    mostrar_correo = serializers.BooleanField(read_only=True)
    activo = serializers.BooleanField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_actualizacion = serializers.DateTimeField(read_only=True)
    edad = serializers.IntegerField(read_only=True)
    anos_en_institucion = serializers.IntegerField(read_only=True)


class ProfileListSerializer(serializers.Serializer):
    """
    Serializer para listar perfiles (solo campos públicos)
    """
    id = serializers.IntegerField(read_only=True)
    usuario_id = serializers.IntegerField(read_only=True)
    cargo = serializers.CharField(read_only=True)
    departamento = serializers.CharField(read_only=True)
    fecha_ingreso = serializers.DateField(read_only=True)
    biografia = serializers.CharField(read_only=True)
    avatar_url = serializers.URLField(read_only=True)
    telefono = serializers.CharField(read_only=True)  # Solo si mostrar_telefono es True
    edad = serializers.IntegerField(read_only=True)
    anos_en_institucion = serializers.IntegerField(read_only=True)


class SyncUserDataSerializer(serializers.Serializer):
    """
    Serializer para sincronización con auth_service
    """
    usuario_id = serializers.IntegerField(min_value=1)
    departamento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    cargo = serializers.CharField(max_length=100, required=False, allow_blank=True)


class ProfileStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de perfiles
    """
    total_profiles = serializers.IntegerField(read_only=True)
    profiles_publicos = serializers.IntegerField(read_only=True)
    profiles_por_departamento = serializers.DictField(read_only=True)
    promedio_anos_institucion = serializers.FloatField(read_only=True)


# DTOs para respuestas de API
class ApiResponseSerializer(serializers.Serializer):
    """
    Formato estándar de respuesta de la API
    """
    exito = serializers.BooleanField()
    mensaje = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)
    errores = serializers.DictField(required=False)
    total = serializers.IntegerField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """
    Formato de respuesta de error
    """
    exito = serializers.BooleanField(default=False)
    mensaje = serializers.CharField()
    errores = serializers.DictField(required=False)
    codigo_error = serializers.CharField(required=False)
