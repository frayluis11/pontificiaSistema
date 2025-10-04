"""
Modelos para el microservicio de reportes

Define los modelos Reporte y Metrica con todas las relaciones
y lógica de negocio para el sistema de reportes.
"""

import uuid
import json
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date


class BaseModel(models.Model):
    """
    Modelo base con campos comunes para auditoría
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True


class TipoReporte(models.TextChoices):
    """Tipos de reportes disponibles"""
    ASISTENCIA = 'ASISTENCIA', 'Reporte de Asistencia'
    PAGOS = 'PAGOS', 'Reporte de Pagos'
    ESTUDIANTES = 'ESTUDIANTES', 'Reporte de Estudiantes'
    METRICAS = 'METRICAS', 'Reporte de Métricas'
    FINANCIERO = 'FINANCIERO', 'Reporte Financiero'
    ACADEMICO = 'ACADEMICO', 'Reporte Académico'
    ADMINISTRATIVO = 'ADMINISTRATIVO', 'Reporte Administrativo'
    PERSONALIZADO = 'PERSONALIZADO', 'Reporte Personalizado'


class FormatoReporte(models.TextChoices):
    """Formatos de exportación disponibles"""
    PDF = 'PDF', 'PDF'
    EXCEL = 'EXCEL', 'Excel'
    CSV = 'CSV', 'CSV'
    JSON = 'JSON', 'JSON'


class EstadoReporte(models.TextChoices):
    """Estados del reporte"""
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    PROCESANDO = 'PROCESANDO', 'Procesando'
    COMPLETADO = 'COMPLETADO', 'Completado'
    ERROR = 'ERROR', 'Error'
    CANCELADO = 'CANCELADO', 'Cancelado'


class Reporte(BaseModel):
    """
    Modelo principal para reportes del sistema
    
    Almacena información sobre reportes generados, sus parámetros,
    estado y archivos asociados.
    """
    
    nombre = models.CharField(
        max_length=255,
        help_text="Nombre descriptivo del reporte"
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada del reporte"
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TipoReporte.choices,
        default=TipoReporte.PERSONALIZADO,
        help_text="Tipo de reporte"
    )
    
    formato = models.CharField(
        max_length=10,
        choices=FormatoReporte.choices,
        default=FormatoReporte.PDF,
        help_text="Formato de exportación"
    )
    
    estado = models.CharField(
        max_length=15,
        choices=EstadoReporte.choices,
        default=EstadoReporte.PENDIENTE,
        help_text="Estado actual del reporte"
    )
    
    # Parámetros del reporte almacenados como JSON
    parametros = models.JSONField(
        default=dict,
        help_text="Parámetros de configuración del reporte"
    )
    
    # Usuario que solicitó el reporte  
    autor_id = models.CharField(
        max_length=50,
        help_text="ID del usuario que solicitó el reporte"
    )
    
    autor_nombre = models.CharField(
        max_length=255,
        help_text="Nombre del usuario que solicitó el reporte"
    )
    
    autor_email = models.EmailField(
        blank=True,
        help_text="Email del usuario para notificaciones"
    )
    
    # Fechas de procesamiento
    fecha_inicio_procesamiento = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha y hora de inicio del procesamiento"
    )
    
    fecha_fin_procesamiento = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha y hora de finalización del procesamiento"
    )
    
    # Archivo generado
    archivo = models.FileField(
        upload_to='reportes/%Y/%m/',
        null=True, blank=True,
        help_text="Archivo del reporte generado"
    )
    
    archivo_nombre = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nombre original del archivo"
    )
    
    archivo_tamaño = models.PositiveIntegerField(
        default=0,
        help_text="Tamaño del archivo en bytes"
    )
    
    # Información de procesamiento
    tiempo_procesamiento = models.DurationField(
        null=True, blank=True,
        help_text="Tiempo total de procesamiento"
    )
    
    registros_procesados = models.PositiveIntegerField(
        default=0,
        help_text="Número de registros procesados"
    )
    
    mensaje_error = models.TextField(
        blank=True,
        help_text="Mensaje de error si el procesamiento falló"
    )
    
    # Configuración de notificaciones
    notificar_por_email = models.BooleanField(
        default=True,
        help_text="Enviar notificación por email al completar"
    )
    
    # Configuración de acceso
    publico = models.BooleanField(
        default=False,
        help_text="Reporte público (visible para otros usuarios)"
    )
    
    fecha_expiracion = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha de expiración del reporte"
    )
    
    # Metadatos adicionales
    tags = models.JSONField(
        default=list,
        help_text="Etiquetas para categorizar el reporte"
    )
    
    version = models.PositiveIntegerField(
        default=1,
        help_text="Versión del reporte"
    )

    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['tipo', 'estado']),
            models.Index(fields=['autor_id']),
            models.Index(fields=['fecha_creacion']),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.tipo} ({self.estado})"

    def clean(self):
        """Validaciones personalizadas"""
        # Validar parámetros según el tipo de reporte
        if self.tipo and not isinstance(self.parametros, dict):
            raise ValidationError("Los parámetros deben ser un objeto JSON válido")
        
        # Validar fechas
        if self.fecha_expiracion and self.fecha_expiracion <= timezone.now():
            raise ValidationError("La fecha de expiración debe ser futura")

    def save(self, *args, **kwargs):
        """Override save para lógica adicional"""
        self.clean()
        
        # Generar nombre de archivo si no existe
        if not self.archivo_nombre and self.nombre:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            self.archivo_nombre = f"{self.nombre}_{timestamp}.{self.formato.lower()}"
        
        super().save(*args, **kwargs)

    def iniciar_procesamiento(self):
        """Marca el reporte como en procesamiento"""
        self.estado = EstadoReporte.PROCESANDO
        self.fecha_inicio_procesamiento = timezone.now()
        self.save(update_fields=['estado', 'fecha_inicio_procesamiento'])

    def completar_procesamiento(self, archivo_path=None, registros=0):
        """Marca el reporte como completado"""
        self.estado = EstadoReporte.COMPLETADO
        self.fecha_fin_procesamiento = timezone.now()
        self.registros_procesados = registros
        
        if self.fecha_inicio_procesamiento:
            self.tiempo_procesamiento = self.fecha_fin_procesamiento - self.fecha_inicio_procesamiento
        
        if archivo_path:
            # Actualizar información del archivo
            import os
            if os.path.exists(archivo_path):
                self.archivo_tamaño = os.path.getsize(archivo_path)
        
        self.save(update_fields=[
            'estado', 'fecha_fin_procesamiento', 'registros_procesados',
            'tiempo_procesamiento', 'archivo_tamaño'
        ])

    def marcar_error(self, mensaje_error):
        """Marca el reporte con error"""
        self.estado = EstadoReporte.ERROR
        self.mensaje_error = mensaje_error
        self.fecha_fin_procesamiento = timezone.now()
        
        if self.fecha_inicio_procesamiento:
            self.tiempo_procesamiento = self.fecha_fin_procesamiento - self.fecha_inicio_procesamiento
        
        self.save(update_fields=[
            'estado', 'mensaje_error', 'fecha_fin_procesamiento', 'tiempo_procesamiento'
        ])

    def cancelar(self):
        """Cancela el reporte"""
        self.estado = EstadoReporte.CANCELADO
        self.fecha_fin_procesamiento = timezone.now()
        
        if self.fecha_inicio_procesamiento:
            self.tiempo_procesamiento = self.fecha_fin_procesamiento - self.fecha_inicio_procesamiento
        
        self.save(update_fields=['estado', 'fecha_fin_procesamiento', 'tiempo_procesamiento'])

    def esta_expirado(self):
        """Verifica si el reporte está expirado"""
        if not self.fecha_expiracion:
            return False
        return timezone.now() > self.fecha_expiracion

    def puede_descargar(self, user_id=None):
        """Verifica si un usuario puede descargar el reporte"""
        if self.esta_expirado():
            return False
        
        if self.publico:
            return True
        
        return str(user_id) == str(self.autor_id)

    def get_parametros_display(self):
        """Devuelve los parámetros en formato legible"""
        if not self.parametros:
            return "Sin parámetros"
        
        try:
            return json.dumps(self.parametros, indent=2, ensure_ascii=False)
        except:
            return str(self.parametros)


class TipoMetrica(models.TextChoices):
    """Tipos de métricas disponibles"""
    CONTADOR = 'CONTADOR', 'Contador'
    PORCENTAJE = 'PORCENTAJE', 'Porcentaje'
    PROMEDIO = 'PROMEDIO', 'Promedio'
    SUMA = 'SUMA', 'Suma'
    MAXIMO = 'MAXIMO', 'Máximo'
    MINIMO = 'MINIMO', 'Mínimo'
    RATIO = 'RATIO', 'Ratio'


class PeriodoMetrica(models.TextChoices):
    """Períodos de métricas"""
    DIARIO = 'DIARIO', 'Diario'
    SEMANAL = 'SEMANAL', 'Semanal'
    MENSUAL = 'MENSUAL', 'Mensual'
    TRIMESTRAL = 'TRIMESTRAL', 'Trimestral'
    ANUAL = 'ANUAL', 'Anual'
    PERSONALIZADO = 'PERSONALIZADO', 'Personalizado'


class Metrica(BaseModel):
    """
    Modelo para almacenar métricas del sistema
    
    Permite almacenar diferentes tipos de métricas con sus valores
    y períodos correspondientes.
    """
    
    nombre = models.CharField(
        max_length=255,
        help_text="Nombre de la métrica"
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción de la métrica"
    )
    
    tipo = models.CharField(
        max_length=15,
        choices=TipoMetrica.choices,
        default=TipoMetrica.CONTADOR,
        help_text="Tipo de métrica"
    )
    
    # Valor de la métrica
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Valor numérico de la métrica"
    )
    
    # Período de la métrica
    periodo = models.CharField(
        max_length=15,
        choices=PeriodoMetrica.choices,
        default=PeriodoMetrica.DIARIO,
        help_text="Período de la métrica"
    )
    
    fecha_inicio = models.DateField(
        help_text="Fecha de inicio del período"
    )
    
    fecha_fin = models.DateField(
        help_text="Fecha de fin del período"
    )
    
    # Metadatos adicionales
    unidad = models.CharField(
        max_length=50,
        blank=True,
        help_text="Unidad de medida (ej: %, personas, soles)"
    )
    
    categoria = models.CharField(
        max_length=100,
        blank=True,
        help_text="Categoría de la métrica"
    )
    
    etiquetas = models.JSONField(
        default=dict,
        help_text="Etiquetas adicionales para filtrado"
    )
    
    # Información de origen
    fuente = models.CharField(
        max_length=100,
        blank=True,
        help_text="Fuente de datos de la métrica"
    )
    
    autor_calculo_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID del usuario o sistema que calculó la métrica"
    )
    
    fecha_calculo = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora del cálculo"
    )
    
    # Configuración de alertas
    valor_objetivo = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True, blank=True,
        help_text="Valor objetivo para la métrica"
    )
    
    umbral_minimo = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True, blank=True,
        help_text="Umbral mínimo para alertas"
    )
    
    umbral_maximo = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True, blank=True,
        help_text="Umbral máximo para alertas"
    )

    class Meta:
        verbose_name = "Métrica"
        verbose_name_plural = "Métricas"
        ordering = ['-fecha_calculo']
        indexes = [
            models.Index(fields=['nombre', 'periodo']),
            models.Index(fields=['categoria']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
            models.Index(fields=['fecha_calculo']),
        ]
        
        # Constraint para evitar métricas duplicadas
        unique_together = [
            ['nombre', 'periodo', 'fecha_inicio', 'fecha_fin']
        ]

    def __str__(self):
        return f"{self.nombre} - {self.valor} ({self.periodo})"

    def clean(self):
        """Validaciones personalizadas"""
        # Validar fechas
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        # Validar umbrales
        if (self.umbral_minimo is not None and self.umbral_maximo is not None 
            and self.umbral_minimo >= self.umbral_maximo):
            raise ValidationError("El umbral mínimo debe ser menor al umbral máximo")

    def save(self, *args, **kwargs):
        """Override save para lógica adicional"""
        self.clean()
        super().save(*args, **kwargs)

    def esta_en_objetivo(self):
        """Verifica si la métrica está en el objetivo"""
        if self.valor_objetivo is None:
            return None
        
        if self.tipo == TipoMetrica.PORCENTAJE:
            # Para porcentajes, considerar un margen del 5%
            margen = Decimal('0.05') * self.valor_objetivo
            return abs(self.valor - self.valor_objetivo) <= margen
        
        return self.valor >= self.valor_objetivo

    def tiene_alerta(self):
        """Verifica si la métrica tiene alguna alerta"""
        alertas = []
        
        if self.umbral_minimo is not None and self.valor < self.umbral_minimo:
            alertas.append('MINIMO')
        
        if self.umbral_maximo is not None and self.valor > self.umbral_maximo:
            alertas.append('MAXIMO')
        
        return alertas

    def get_porcentaje_objetivo(self):
        """Calcula el porcentaje respecto al objetivo"""
        if self.valor_objetivo is None or self.valor_objetivo == 0:
            return None
        
        return float((self.valor / self.valor_objetivo) * 100)

    def get_variacion_periodo_anterior(self):
        """Obtiene la variación respecto al período anterior"""
        # Buscar métrica del período anterior
        periodo_anterior = None
        
        if self.periodo == PeriodoMetrica.DIARIO:
            from django.utils import timezone
            from datetime import timedelta
            fecha_anterior = self.fecha_inicio - timedelta(days=1)
            periodo_anterior = Metrica.objects.filter(
                nombre=self.nombre,
                periodo=self.periodo,
                fecha_inicio=fecha_anterior
            ).first()
        
        if periodo_anterior:
            if periodo_anterior.valor == 0:
                return None
            
            variacion = ((self.valor - periodo_anterior.valor) / periodo_anterior.valor) * 100
            return float(variacion)
        
        return None


class ReporteMetrica(BaseModel):
    """
    Tabla intermedia para relacionar reportes con métricas
    
    Permite que un reporte incluya múltiples métricas
    """
    
    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        related_name='metricas_incluidas'
    )
    
    metrica = models.ForeignKey(
        Metrica,
        on_delete=models.CASCADE,
        related_name='reportes_incluidos'
    )
    
    # Configuración específica para esta métrica en el reporte
    incluir_grafico = models.BooleanField(
        default=True,
        help_text="Incluir gráfico de esta métrica"
    )
    
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de la métrica en el reporte"
    )
    
    configuracion_grafico = models.JSONField(
        default=dict,
        help_text="Configuración específica del gráfico"
    )

    class Meta:
        verbose_name = "Reporte-Métrica"
        verbose_name_plural = "Reportes-Métricas"
        ordering = ['orden', 'metrica__nombre']
        unique_together = [['reporte', 'metrica']]

    def __str__(self):
        return f"{self.reporte.nombre} - {self.metrica.nombre}"
