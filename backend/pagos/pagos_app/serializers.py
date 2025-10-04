"""
Serializers para el microservicio de pagos

Define todos los DTOs y validaciones para los endpoints REST
"""

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from decimal import Decimal
from datetime import date, datetime
from django.contrib.auth.models import User

from .models import (
    Pago, Planilla, Boleta, Adelanto, Descuento, 
    Bonificacion, PagoDescuento, PagoBonificacion
)
from .utils import validar_periodo_valido


class DescuentoSerializer(serializers.ModelSerializer):
    """Serializer para Descuento"""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    monto_calculado = serializers.SerializerMethodField()
    
    class Meta:
        model = Descuento
        fields = [
            'id', 'nombre', 'tipo', 'tipo_display', 'porcentaje', 'monto_fijo',
            'descripcion', 'obligatorio', 'aplicable_desde', 'aplicable_hasta',
            'monto_calculado', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def get_monto_calculado(self, obj):
        """Calcula el monto para un salario base hipotético"""
        salario_base = self.context.get('salario_base', Decimal('1000.00'))
        return obj.calcular_monto(salario_base)
    
    def validate(self, data):
        """Validaciones del descuento"""
        if not data.get('porcentaje') and not data.get('monto_fijo'):
            raise serializers.ValidationError(
                "Debe especificar porcentaje o monto fijo"
            )
        
        if data.get('porcentaje') and data.get('monto_fijo'):
            raise serializers.ValidationError(
                "No puede especificar porcentaje y monto fijo al mismo tiempo"
            )
        
        if data.get('aplicable_hasta') and data.get('aplicable_desde'):
            if data['aplicable_hasta'] < data['aplicable_desde']:
                raise serializers.ValidationError(
                    "La fecha 'aplicable_hasta' debe ser posterior a 'aplicable_desde'"
                )
        
        return data


class BonificacionSerializer(serializers.ModelSerializer):
    """Serializer para Bonificación"""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    monto_calculado = serializers.SerializerMethodField()
    
    class Meta:
        model = Bonificacion
        fields = [
            'id', 'nombre', 'tipo', 'tipo_display', 'porcentaje', 'monto_fijo',
            'descripcion', 'requiere_aprobacion', 'aplicable_desde', 'aplicable_hasta',
            'monto_calculado', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def get_monto_calculado(self, obj):
        """Calcula el monto para un salario base hipotético"""
        salario_base = self.context.get('salario_base', Decimal('1000.00'))
        return obj.calcular_monto(salario_base)
    
    def validate(self, data):
        """Validaciones de la bonificación"""
        if not data.get('porcentaje') and not data.get('monto_fijo'):
            raise serializers.ValidationError(
                "Debe especificar porcentaje o monto fijo"
            )
        
        if data.get('porcentaje') and data.get('monto_fijo'):
            raise serializers.ValidationError(
                "No puede especificar porcentaje y monto fijo al mismo tiempo"
            )
        
        return data


class PagoDescuentoSerializer(serializers.ModelSerializer):
    """Serializer para PagoDescuento"""
    
    descuento = DescuentoSerializer(read_only=True)
    descuento_id = serializers.UUIDField(write_only=True)
    monto_aplicado = serializers.ReadOnlyField()
    
    class Meta:
        model = PagoDescuento
        fields = [
            'id', 'descuento', 'descuento_id', 'monto_calculado', 
            'monto_personalizado', 'monto_aplicado', 'observaciones'
        ]


class PagoBonificacionSerializer(serializers.ModelSerializer):
    """Serializer para PagoBonificación"""
    
    bonificacion = BonificacionSerializer(read_only=True)
    bonificacion_id = serializers.UUIDField(write_only=True)
    monto_aplicado = serializers.ReadOnlyField()
    
    class Meta:
        model = PagoBonificacion
        fields = [
            'id', 'bonificacion', 'bonificacion_id', 'monto_calculado', 
            'monto_personalizado', 'monto_aplicado', 'observaciones'
        ]


class PlanillaSerializer(serializers.ModelSerializer):
    """Serializer para Planilla"""
    
    nombre_periodo = serializers.SerializerMethodField()
    puede_procesar = serializers.ReadOnlyField()
    puede_aprobar = serializers.ReadOnlyField()
    cantidad_pagos = serializers.SerializerMethodField()
    aprobada_por_nombre = serializers.CharField(source='aprobada_por.get_full_name', read_only=True)
    
    class Meta:
        model = Planilla
        fields = [
            'id', 'nombre', 'nombre_periodo', 'periodo_inicio', 'periodo_fin',
            'año', 'mes', 'total_bruto', 'total_descuentos', 'total_bonificaciones',
            'total_neto', 'cantidad_trabajadores', 'fecha_procesamiento',
            'procesada', 'aprobada', 'fecha_aprobacion', 'aprobada_por',
            'aprobada_por_nombre', 'observaciones', 'puede_procesar', 'puede_aprobar',
            'cantidad_pagos', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'total_bruto', 'total_descuentos', 'total_bonificaciones',
            'total_neto', 'cantidad_trabajadores', 'fecha_procesamiento',
            'fecha_aprobacion', 'creado_en', 'actualizado_en'
        ]
    
    def get_nombre_periodo(self, obj):
        """Genera nombre legible del periodo"""
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return f"{meses.get(obj.mes, obj.mes)} {obj.año}"
    
    def get_cantidad_pagos(self, obj):
        """Cuenta los pagos asociados"""
        return obj.pagos.filter(activo=True).count()
    
    def validate(self, data):
        """Validaciones de la planilla"""
        if not validar_periodo_valido(data.get('año', 0), data.get('mes', 0)):
            raise serializers.ValidationError("Periodo no válido")
        
        # Validar que no exista otra planilla para el mismo periodo
        if self.instance is None:  # Solo al crear
            if Planilla.objects.filter(
                año=data['año'], 
                mes=data['mes'], 
                activo=True
            ).exists():
                raise serializers.ValidationError(
                    f"Ya existe una planilla para {data['año']}-{data['mes']:02d}"
                )
        
        return data


class PagoSerializer(serializers.ModelSerializer):
    """Serializer para Pago"""
    
    planilla = PlanillaSerializer(read_only=True)
    planilla_id = serializers.UUIDField(write_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    descuentos = PagoDescuentoSerializer(source='pagodescuento_set', many=True, read_only=True)
    bonificaciones = PagoBonificacionSerializer(source='pagobonificacion_set', many=True, read_only=True)
    puede_generar_boleta = serializers.ReadOnlyField()
    tiene_boleta = serializers.SerializerMethodField()
    
    class Meta:
        model = Pago
        fields = [
            'id', 'planilla', 'planilla_id', 'trabajador_id', 'trabajador_nombre',
            'trabajador_documento', 'salario_base', 'monto_bruto', 'total_descuentos',
            'total_bonificaciones', 'monto_neto', 'estado', 'estado_display',
            'fecha_calculo', 'fecha_aprobacion', 'fecha_pago', 'dias_trabajados',
            'horas_extras', 'observaciones', 'descuentos', 'bonificaciones',
            'puede_generar_boleta', 'tiene_boleta', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'monto_bruto', 'total_descuentos', 'total_bonificaciones',
            'monto_neto', 'fecha_calculo', 'fecha_aprobacion', 'fecha_pago',
            'creado_en', 'actualizado_en'
        ]
    
    def get_tiene_boleta(self, obj):
        """Verifica si tiene boleta generada"""
        return hasattr(obj, 'boleta') and obj.boleta is not None
    
    def validate_trabajador_id(self, value):
        """Valida que el trabajador_id sea válido"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("ID de trabajador es requerido")
        return value.strip()
    
    def validate_salario_base(self, value):
        """Valida el salario base"""
        if value <= 0:
            raise serializers.ValidationError("El salario base debe ser mayor a 0")
        
        # Validar salario mínimo (RMV 2024)
        salario_minimo = Decimal('1025.00')
        if value < salario_minimo:
            raise serializers.ValidationError(
                f"El salario base no puede ser menor al salario mínimo (S/ {salario_minimo})"
            )
        
        return value
    
    def validate_dias_trabajados(self, value):
        """Valida los días trabajados"""
        if value < 0 or value > 31:
            raise serializers.ValidationError("Los días trabajados deben estar entre 0 y 31")
        return value


class BoletaSerializer(serializers.ModelSerializer):
    """Serializer para Boleta"""
    
    pago = PagoSerializer(read_only=True)
    pago_id = serializers.UUIDField(write_only=True)
    generada_por_nombre = serializers.CharField(source='generada_por.get_full_name', read_only=True)
    tamaño_archivo_mb = serializers.SerializerMethodField()
    puede_regenerar = serializers.ReadOnlyField()
    url_descarga = serializers.SerializerMethodField()
    
    class Meta:
        model = Boleta
        fields = [
            'id', 'pago', 'pago_id', 'numero_boleta', 'archivo_pdf',
            'fecha_generacion', 'generada_por', 'generada_por_nombre',
            'tamaño_archivo', 'tamaño_archivo_mb', 'hash_archivo',
            'version', 'boleta_anterior', 'enviada_por_email',
            'fecha_envio_email', 'puede_regenerar', 'url_descarga',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'numero_boleta', 'fecha_generacion', 'tamaño_archivo',
            'hash_archivo', 'creado_en', 'actualizado_en'
        ]
    
    def get_tamaño_archivo_mb(self, obj):
        """Convierte el tamaño a MB"""
        if obj.tamaño_archivo:
            return round(obj.tamaño_archivo / (1024 * 1024), 2)
        return None
    
    def get_url_descarga(self, obj):
        """URL para descargar la boleta"""
        if obj.archivo_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo_pdf.url)
        return None


class AdelantoSerializer(serializers.ModelSerializer):
    """Serializer para Adelanto"""
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    aprobado_por_nombre = serializers.CharField(source='aprobado_por.get_full_name', read_only=True)
    pago_descuento_detalle = serializers.SerializerMethodField()
    puede_aprobar = serializers.SerializerMethodField()
    
    class Meta:
        model = Adelanto
        fields = [
            'id', 'trabajador_id', 'trabajador_nombre', 'monto_solicitado',
            'monto_aprobado', 'fecha_solicitud', 'fecha_aprobacion',
            'fecha_descuento', 'estado', 'estado_display', 'motivo',
            'observaciones_aprobacion', 'aprobado_por', 'aprobado_por_nombre',
            'pago_descuento', 'pago_descuento_detalle', 'puede_aprobar',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'fecha_solicitud', 'fecha_aprobacion', 'fecha_descuento',
            'estado', 'observaciones_aprobacion', 'aprobado_por', 'pago_descuento',
            'creado_en', 'actualizado_en'
        ]
    
    def get_pago_descuento_detalle(self, obj):
        """Detalles del pago donde se aplicó el descuento"""
        if obj.pago_descuento:
            return {
                'planilla': f"{obj.pago_descuento.planilla.año}-{obj.pago_descuento.planilla.mes:02d}",
                'monto_neto': obj.pago_descuento.monto_neto
            }
        return None
    
    def get_puede_aprobar(self, obj):
        """Verifica si puede ser aprobado"""
        return obj.estado == 'SOLICITADO'
    
    def validate_monto_solicitado(self, value):
        """Valida el monto solicitado"""
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        
        # Validar límite máximo
        limite_maximo = Decimal('5000.00')  # Límite configurable
        if value > limite_maximo:
            raise serializers.ValidationError(
                f"El monto no puede exceder S/ {limite_maximo}"
            )
        
        return value
    
    def validate_trabajador_id(self, value):
        """Valida el ID del trabajador"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("ID de trabajador es requerido")
        return value.strip()


# Serializers para endpoints específicos

class GenerarPlanillaSerializer(serializers.Serializer):
    """Serializer para generar planilla"""
    
    año = serializers.IntegerField(min_value=2020, max_value=2030)
    mes = serializers.IntegerField(min_value=1, max_value=12)
    trabajadores = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=1000
    )
    
    def validate_trabajadores(self, value):
        """Valida la lista de trabajadores"""
        required_fields = ['trabajador_id', 'trabajador_nombre', 'trabajador_documento', 'salario_base']
        
        for i, trabajador in enumerate(value):
            for field in required_fields:
                if field not in trabajador:
                    raise serializers.ValidationError(
                        f"Trabajador {i+1}: campo '{field}' es requerido"
                    )
            
            # Validar salario base
            try:
                salario = Decimal(str(trabajador['salario_base']))
                if salario <= 0:
                    raise serializers.ValidationError(
                        f"Trabajador {i+1}: salario base debe ser mayor a 0"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Trabajador {i+1}: salario base no es válido"
                )
        
        return value
    
    def validate(self, data):
        """Validación general"""
        if not validar_periodo_valido(data['año'], data['mes']):
            raise serializers.ValidationError("Periodo no válido")
        
        # Verificar que no exista planilla para el periodo
        if Planilla.objects.filter(año=data['año'], mes=data['mes'], activo=True).exists():
            raise serializers.ValidationError(
                f"Ya exists planilla para {data['año']}-{data['mes']:02d}"
            )
        
        return data


class AprobarPlanillaSerializer(serializers.Serializer):
    """Serializer para aprobar planilla"""
    
    observaciones = serializers.CharField(required=False, allow_blank=True, max_length=500)


class GenerarBoletaSerializer(serializers.Serializer):
    """Serializer para generar boleta"""
    
    pago_id = serializers.UUIDField()
    enviar_email = serializers.BooleanField(default=False)
    email_trabajador = serializers.EmailField(required=False)
    
    def validate(self, data):
        """Validación para generar boleta"""
        if data.get('enviar_email') and not data.get('email_trabajador'):
            raise serializers.ValidationError(
                "Email del trabajador es requerido para envío automático"
            )
        
        return data


class AprobarAdelantoSerializer(serializers.Serializer):
    """Serializer para aprobar adelanto"""
    
    monto_aprobado = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        min_value=Decimal('0.01')
    )
    observaciones = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_monto_aprobado(self, value):
        """Valida el monto aprobado"""
        if value and value <= 0:
            raise serializers.ValidationError("El monto aprobado debe ser mayor a 0")
        return value


class RechazarAdelantoSerializer(serializers.Serializer):
    """Serializer para rechazar adelanto"""
    
    observaciones = serializers.CharField(required=True, max_length=500)
    
    def validate_observaciones(self, value):
        """Valida que haya observaciones para el rechazo"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError(
                "Las observaciones son requeridas para rechazar un adelanto"
            )
        return value.strip()


class ResumenTrabajadorSerializer(serializers.Serializer):
    """Serializer para resumen de trabajador"""
    
    trabajador_id = serializers.CharField(read_only=True)
    año = serializers.IntegerField(read_only=True)
    pagos = serializers.DictField(read_only=True)
    adelantos = serializers.DictField(read_only=True)
    ultimo_pago = serializers.DictField(read_only=True)
    boletas_generadas = serializers.IntegerField(read_only=True)


class EstadisticasPagosSerializer(serializers.Serializer):
    """Serializer para estadísticas de pagos"""
    
    periodo = serializers.CharField(read_only=True)
    total_trabajadores = serializers.IntegerField(read_only=True)
    total_bruto = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_descuentos = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_bonificaciones = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_neto = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    promedio_salario = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pagos_por_estado = serializers.ListField(read_only=True)