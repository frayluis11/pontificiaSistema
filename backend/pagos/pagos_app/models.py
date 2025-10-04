"""
Modelos para el microservicio de pagos

Incluye los modelos principales:
- Pago: Registro principal de pagos de trabajadores
- Planilla: Agrupación de pagos por periodo
- Boleta: Documento PDF de pago individual
- Adelanto: Adelantos de sueldo
- Descuento: Descuentos aplicables
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date, datetime
import uuid


class BaseModel(models.Model):
    """
    Modelo base con campos comunes para auditoría
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True


class TipoDescuento(models.TextChoices):
    """Tipos de descuentos disponibles"""
    ESSALUD = 'ESSALUD', 'EsSalud (9%)'
    ONP = 'ONP', 'ONP (13%)'
    AFP = 'AFP', 'AFP'
    QUINTA_CATEGORIA = 'QUINTA', 'Quinta Categoría'
    PRESTAMO = 'PRESTAMO', 'Préstamo'
    ADELANTO = 'ADELANTO', 'Adelanto'
    OTROS = 'OTROS', 'Otros'


class TipoBonificacion(models.TextChoices):
    """Tipos de bonificaciones disponibles"""
    ASIGNACION_FAMILIAR = 'ASIG_FAM', 'Asignación Familiar'
    BONO_PRODUCTIVIDAD = 'PRODUCTIVIDAD', 'Bono Productividad'
    HORAS_EXTRAS = 'HORAS_EXTRAS', 'Horas Extras'
    GRATIFICACION = 'GRATIFICACION', 'Gratificación'
    CTS = 'CTS', 'CTS'
    VACACIONES = 'VACACIONES', 'Vacaciones'
    OTROS = 'OTROS', 'Otros'


class EstadoPago(models.TextChoices):
    """Estados del pago"""
    CALCULADO = 'CALCULADO', 'Calculado'
    APROBADO = 'APROBADO', 'Aprobado'
    PAGADO = 'PAGADO', 'Pagado'
    ANULADO = 'ANULADO', 'Anulado'


class Descuento(BaseModel):
    """
    Modelo para diferentes tipos de descuentos
    """
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TipoDescuento.choices)
    porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    monto_fijo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    descripcion = models.TextField(blank=True)
    obligatorio = models.BooleanField(default=False)
    aplicable_desde = models.DateField(default=date.today)
    aplicable_hasta = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    def calcular_monto(self, salario_bruto):
        """Calcula el monto del descuento basado en el salario bruto"""
        if self.porcentaje:
            return salario_bruto * (self.porcentaje / 100)
        elif self.monto_fijo:
            return self.monto_fijo
        return Decimal('0.00')

    def es_aplicable(self, fecha=None):
        """Verifica si el descuento es aplicable en una fecha específica"""
        if fecha is None:
            fecha = date.today()
        
        if fecha < self.aplicable_desde:
            return False
        
        if self.aplicable_hasta and fecha > self.aplicable_hasta:
            return False
        
        return self.activo


class Bonificacion(BaseModel):
    """
    Modelo para diferentes tipos de bonificaciones
    """
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TipoBonificacion.choices)
    porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    monto_fijo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    descripcion = models.TextField(blank=True)
    requiere_aprobacion = models.BooleanField(default=False)
    aplicable_desde = models.DateField(default=date.today)
    aplicable_hasta = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Bonificación'
        verbose_name_plural = 'Bonificaciones'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    def calcular_monto(self, salario_bruto):
        """Calcula el monto de la bonificación basado en el salario bruto"""
        if self.porcentaje:
            return salario_bruto * (self.porcentaje / 100)
        elif self.monto_fijo:
            return self.monto_fijo
        return Decimal('0.00')

    def es_aplicable(self, fecha=None):
        """Verifica si la bonificación es aplicable en una fecha específica"""
        if fecha is None:
            fecha = date.today()
        
        if fecha < self.aplicable_desde:
            return False
        
        if self.aplicable_hasta and fecha > self.aplicable_hasta:
            return False
        
        return self.activo


class Planilla(BaseModel):
    """
    Modelo para planillas de pagos por periodo
    """
    nombre = models.CharField(max_length=100)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    año = models.IntegerField()
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    total_bruto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_descuentos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_bonificaciones = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_neto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cantidad_trabajadores = models.IntegerField(default=0)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    procesada = models.BooleanField(default=False)
    aprobada = models.BooleanField(default=False)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    aprobada_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='planillas_aprobadas'
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Planilla'
        verbose_name_plural = 'Planillas'
        ordering = ['-año', '-mes']
        unique_together = ['año', 'mes']

    def __str__(self):
        return f"Planilla {self.año}-{self.mes:02d}: {self.nombre}"

    def generar_nombre_automatico(self):
        """Genera un nombre automático para la planilla"""
        meses = [
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        return f"Planilla {meses[self.mes]} {self.año}"

    def calcular_totales(self):
        """Calcula los totales de la planilla basado en los pagos asociados"""
        pagos = self.pagos.filter(activo=True)
        
        self.total_bruto = sum(pago.monto_bruto for pago in pagos)
        self.total_descuentos = sum(pago.total_descuentos for pago in pagos)
        self.total_bonificaciones = sum(pago.total_bonificaciones for pago in pagos)
        self.total_neto = sum(pago.monto_neto for pago in pagos)
        self.cantidad_trabajadores = pagos.count()

    def puede_procesar(self):
        """Verifica si la planilla puede ser procesada"""
        return not self.procesada and self.pagos.filter(activo=True).exists()

    def puede_aprobar(self):
        """Verifica si la planilla puede ser aprobada"""
        return self.procesada and not self.aprobada

    def save(self, *args, **kwargs):
        if not self.nombre:
            self.nombre = self.generar_nombre_automatico()
        super().save(*args, **kwargs)


class Pago(BaseModel):
    """
    Modelo principal para pagos de trabajadores
    """
    planilla = models.ForeignKey(Planilla, on_delete=models.CASCADE, related_name='pagos')
    trabajador_id = models.CharField(max_length=20, db_index=True)  # ID del trabajador del microservicio de personal
    trabajador_nombre = models.CharField(max_length=200)  # Nombre para desnormalización
    trabajador_documento = models.CharField(max_length=20)  # Documento para búsqueda
    
    # Montos principales
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    monto_bruto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_descuentos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_bonificaciones = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Estado y fechas
    estado = models.CharField(max_length=20, choices=EstadoPago.choices, default=EstadoPago.CALCULADO)
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    
    # Información adicional
    dias_trabajados = models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(31)])
    horas_extras = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True)
    
    # Relaciones con descuentos y bonificaciones aplicados
    descuentos_aplicados = models.ManyToManyField(Descuento, through='PagoDescuento', blank=True)
    bonificaciones_aplicadas = models.ManyToManyField(Bonificacion, through='PagoBonificacion', blank=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_calculo']
        unique_together = ['planilla', 'trabajador_id']

    def __str__(self):
        return f"Pago {self.trabajador_nombre} - {self.planilla.año}-{self.planilla.mes:02d}"

    def calcular_pago(self):
        """
        Calcula el pago total aplicando descuentos y bonificaciones
        """
        # Calcular salario bruto (base + horas extras + bonificaciones)
        self.monto_bruto = self.salario_base
        
        # Aplicar bonificaciones
        total_bonificaciones = Decimal('0.00')
        for pago_bonificacion in self.pagobonificacion_set.all():
            bonificacion_monto = pago_bonificacion.bonificacion.calcular_monto(self.salario_base)
            if pago_bonificacion.monto_personalizado:
                bonificacion_monto = pago_bonificacion.monto_personalizado
            total_bonificaciones += bonificacion_monto
        
        self.total_bonificaciones = total_bonificaciones
        self.monto_bruto += total_bonificaciones
        
        # Aplicar descuentos
        total_descuentos = Decimal('0.00')
        for pago_descuento in self.pagodescuento_set.all():
            descuento_monto = pago_descuento.descuento.calcular_monto(self.monto_bruto)
            if pago_descuento.monto_personalizado:
                descuento_monto = pago_descuento.monto_personalizado
            total_descuentos += descuento_monto
        
        self.total_descuentos = total_descuentos
        
        # Calcular monto neto
        self.monto_neto = self.monto_bruto - total_descuentos
        
        # Asegurar que el monto neto no sea negativo
        if self.monto_neto < 0:
            self.monto_neto = Decimal('0.00')

    def aprobar(self, usuario=None):
        """Aprueba el pago"""
        if self.estado == EstadoPago.CALCULADO:
            self.estado = EstadoPago.APROBADO
            self.fecha_aprobacion = datetime.now()
            if usuario:
                self.creado_por = usuario
            self.save()

    def marcar_como_pagado(self):
        """Marca el pago como pagado"""
        if self.estado == EstadoPago.APROBADO:
            self.estado = EstadoPago.PAGADO
            self.fecha_pago = datetime.now()
            self.save()

    def anular(self):
        """Anula el pago"""
        self.estado = EstadoPago.ANULADO
        self.save()

    def puede_generar_boleta(self):
        """Verifica si se puede generar la boleta de pago"""
        return self.estado in [EstadoPago.APROBADO, EstadoPago.PAGADO]


class PagoDescuento(BaseModel):
    """
    Tabla intermedia para descuentos aplicados a un pago específico
    """
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE)
    descuento = models.ForeignKey(Descuento, on_delete=models.CASCADE)
    monto_calculado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_personalizado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Descuento de Pago'
        verbose_name_plural = 'Descuentos de Pago'
        unique_together = ['pago', 'descuento']

    def __str__(self):
        return f"{self.descuento.nombre} - {self.pago.trabajador_nombre}"

    @property
    def monto_aplicado(self):
        """Retorna el monto aplicado (personalizado o calculado)"""
        return self.monto_personalizado if self.monto_personalizado else self.monto_calculado


class PagoBonificacion(BaseModel):
    """
    Tabla intermedia para bonificaciones aplicadas a un pago específico
    """
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE)
    bonificacion = models.ForeignKey(Bonificacion, on_delete=models.CASCADE)
    monto_calculado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_personalizado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Bonificación de Pago'
        verbose_name_plural = 'Bonificaciones de Pago'
        unique_together = ['pago', 'bonificacion']

    def __str__(self):
        return f"{self.bonificacion.nombre} - {self.pago.trabajador_nombre}"

    @property
    def monto_aplicado(self):
        """Retorna el monto aplicado (personalizado o calculado)"""
        return self.monto_personalizado if self.monto_personalizado else self.monto_calculado


class Adelanto(BaseModel):
    """
    Modelo para adelantos de sueldo
    """
    trabajador_id = models.CharField(max_length=20, db_index=True)
    trabajador_nombre = models.CharField(max_length=200)
    monto_solicitado = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    monto_aprobado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_descuento = models.DateField(null=True, blank=True, help_text="Fecha en que se descontará del sueldo")
    
    estado = models.CharField(
        max_length=20,
        choices=[
            ('SOLICITADO', 'Solicitado'),
            ('APROBADO', 'Aprobado'),
            ('DESCONTADO', 'Descontado'),
            ('RECHAZADO', 'Rechazado'),
        ],
        default='SOLICITADO'
    )
    
    motivo = models.TextField()
    observaciones_aprobacion = models.TextField(blank=True)
    aprobado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='adelantos_aprobados'
    )
    
    # Relación con el pago donde se aplicará el descuento
    pago_descuento = models.ForeignKey(
        Pago, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='adelantos_descontados'
    )

    class Meta:
        verbose_name = 'Adelanto'
        verbose_name_plural = 'Adelantos'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Adelanto {self.trabajador_nombre} - S/ {self.monto_solicitado}"

    def aprobar(self, monto_aprobado=None, usuario=None, observaciones=''):
        """Aprueba el adelanto"""
        if self.estado == 'SOLICITADO':
            self.estado = 'APROBADO'
            self.monto_aprobado = monto_aprobado or self.monto_solicitado
            self.fecha_aprobacion = datetime.now()
            self.aprobado_por = usuario
            self.observaciones_aprobacion = observaciones
            self.save()

    def rechazar(self, observaciones='', usuario=None):
        """Rechaza el adelanto"""
        if self.estado == 'SOLICITADO':
            self.estado = 'RECHAZADO'
            self.observaciones_aprobacion = observaciones
            self.aprobado_por = usuario
            self.save()

    def marcar_como_descontado(self, pago):
        """Marca el adelanto como descontado en un pago específico"""
        if self.estado == 'APROBADO':
            self.estado = 'DESCONTADO'
            self.pago_descuento = pago
            self.save()


class Boleta(BaseModel):
    """
    Modelo para boletas de pago (PDFs)
    """
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='boleta')
    numero_boleta = models.CharField(max_length=50, unique=True, db_index=True)
    archivo_pdf = models.FileField(upload_to='boletas/%Y/%m/', null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    generada_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='boletas_generadas'
    )
    
    # Metadatos del archivo
    tamaño_archivo = models.IntegerField(null=True, blank=True)  # en bytes
    hash_archivo = models.CharField(max_length=64, null=True, blank=True)  # SHA-256
    
    # Control de versiones
    version = models.IntegerField(default=1)
    boleta_anterior = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='versiones_posteriores'
    )
    
    enviada_por_email = models.BooleanField(default=False)
    fecha_envio_email = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Boleta de Pago'
        verbose_name_plural = 'Boletas de Pago'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"Boleta {self.numero_boleta} - {self.pago.trabajador_nombre}"

    def generar_numero_boleta(self):
        """Genera un número único para la boleta"""
        from django.conf import settings
        año = self.pago.planilla.año
        mes = self.pago.planilla.mes
        
        # Contar boletas del mismo mes y año
        count = Boleta.objects.filter(
            pago__planilla__año=año,
            pago__planilla__mes=mes
        ).count() + 1
        
        return settings.PAGOS_CONFIG['FORMATO_NUMERO_BOLETA'].format(
            year=año,
            month=mes,
            numero=count
        )

    def save(self, *args, **kwargs):
        if not self.numero_boleta:
            self.numero_boleta = self.generar_numero_boleta()
        super().save(*args, **kwargs)

    def puede_regenerar(self):
        """Verifica si la boleta puede ser regenerada"""
        return self.pago.estado in [EstadoPago.APROBADO, EstadoPago.PAGADO]
