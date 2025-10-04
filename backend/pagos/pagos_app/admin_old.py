"""
Configuración del admin para el microservicio de pagos

Proporciona interfaces de administración para todos los modelos
del sistema de pagos con funcionalidades avanzadas.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from decimal import Decimal

from .models import (
    Pago, Planilla, Boleta, Adelanto, Descuento, 
    Bonificacion, PagoDescuento, PagoBonificacion
)


class PagoDescuentoInline(admin.TabularInline):
    """Inline para descuentos de un pago"""
    model = PagoDescuento
    extra = 0
    readonly_fields = ('monto_calculado',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('descuento')


class PagoBonificacionInline(admin.TabularInline):
    """Inline para bonificaciones de un pago"""
    model = PagoBonificacion
    extra = 0
    readonly_fields = ('monto_calculado',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bonificacion')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """Administración de pagos"""
    
    list_display = [
        'trabajador_nombre', 'trabajador_documento', 'planilla_info',
        'monto_bruto_formatted', 'monto_descuentos_formatted', 
        'monto_bonificaciones_formatted', 'monto_neto_formatted',
        'estado_badge', 'fecha_calculo'
    ]
    
    list_filter = [
        'estado', 'planilla__año', 'planilla__mes', 
        'fecha_calculo', 'fecha_aprobacion'
    ]
    
    search_fields = [
        'trabajador_nombre', 'trabajador_documento', 
        'trabajador_id', 'planilla__nombre'
    ]
    
    readonly_fields = [
        'id', 'fecha_creacion', 'fecha_actualizacion',
        'fecha_calculo', 'fecha_aprobacion', 'fecha_pago',
        'monto_descuentos', 'monto_bonificaciones', 'monto_neto'
    ]
    
    fieldsets = (
        ('Información del Trabajador', {
            'fields': ('trabajador_id', 'trabajador_nombre', 'trabajador_documento')
        }),
        ('Información de Pago', {
            'fields': ('planilla', 'monto_bruto', 'monto_descuentos', 
                      'monto_bonificaciones', 'monto_neto')
        }),
        ('Estado y Fechas', {
            'fields': ('estado', 'fecha_calculo', 'fecha_aprobacion', 'fecha_pago')
        }),
        ('Metadatos', {
            'fields': ('id', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [PagoDescuentoInline, PagoBonificacionInline]
    
    actions = ['aprobar_pagos', 'marcar_como_pagados']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'planilla'
        ).prefetch_related(
            'pagodescuento_set__descuento',
            'pagobonificacion_set__bonificacion'
        )
    
    def planilla_info(self, obj):
        """Información de la planilla"""
        if obj.planilla:
            return f"{obj.planilla.nombre} ({obj.planilla.año}-{obj.planilla.mes:02d})"
        return "Sin planilla"
    planilla_info.short_description = "Planilla"
    
    def monto_bruto_formatted(self, obj):
        """Monto bruto formateado"""
        return f"S/ {obj.monto_bruto:,.2f}"
    monto_bruto_formatted.short_description = "Monto Bruto"
    monto_bruto_formatted.admin_order_field = 'monto_bruto'
    
    def monto_descuentos_formatted(self, obj):
        """Monto descuentos formateado"""
        return f"S/ {obj.monto_descuentos:,.2f}"
    monto_descuentos_formatted.short_description = "Descuentos"
    monto_descuentos_formatted.admin_order_field = 'monto_descuentos'
    
    def monto_bonificaciones_formatted(self, obj):
        """Monto bonificaciones formateado"""
        return f"S/ {obj.monto_bonificaciones:,.2f}"
    monto_bonificaciones_formatted.short_description = "Bonificaciones"
    monto_bonificaciones_formatted.admin_order_field = 'monto_bonificaciones'
    
    def monto_neto_formatted(self, obj):
        """Monto neto formateado"""
        return f"S/ {obj.monto_neto:,.2f}"
    monto_neto_formatted.short_description = "Monto Neto"
    monto_neto_formatted.admin_order_field = 'monto_neto'
    
    def estado_badge(self, obj):
        """Badge del estado del pago"""
        colors = {
            'CALCULADO': 'blue',
            'APROBADO': 'green',
            'PAGADO': 'purple',
            'ANULADO': 'red'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = "Estado"
    estado_badge.admin_order_field = 'estado'
    
    def aprobar_pagos(self, request, queryset):
        """Acción para aprobar pagos seleccionados"""
        pagos_aprobados = 0
        for pago in queryset.filter(estado='CALCULADO'):
            pago.aprobar(request.user)
            pagos_aprobados += 1
        
        self.message_user(
            request,
            f"Se aprobaron {pagos_aprobados} pagos exitosamente."
        )
    aprobar_pagos.short_description = "Aprobar pagos seleccionados"
    
    def marcar_como_pagados(self, request, queryset):
        """Acción para marcar pagos como pagados"""
        pagos_marcados = 0
        for pago in queryset.filter(estado='APROBADO'):
            pago.marcar_como_pagado()
            pagos_marcados += 1
        
        self.message_user(
            request,
            f"Se marcaron como pagados {pagos_marcados} pagos."
        )
    marcar_como_pagados.short_description = "Marcar como pagados"


class PagoInline(admin.TabularInline):
    """Inline para pagos de una planilla"""
    model = Pago
    extra = 0
    readonly_fields = (
        'trabajador_nombre', 'monto_bruto', 'monto_neto', 
        'estado', 'fecha_calculo'
    )
    fields = readonly_fields
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Planilla)
class PlanillaAdmin(admin.ModelAdmin):
    """Administración de planillas"""
    
    list_display = [
        'nombre', 'año', 'mes', 'total_pagos', 'total_monto_formatted',
        'procesada_badge', 'aprobada_badge', 'fecha_procesamiento'
    ]
    
    list_filter = [
        'año', 'mes', 'procesada', 'aprobada', 
        'fecha_procesamiento', 'fecha_aprobacion'
    ]
    
    search_fields = ['nombre']
    
    readonly_fields = [
        'id', 'fecha_creacion', 'fecha_actualizacion',
        'fecha_procesamiento', 'fecha_aprobacion',
        'total_pagos', 'total_monto'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'año', 'mes')
        }),
        ('Estado', {
            'fields': ('procesada', 'aprobada', 'fecha_procesamiento', 'fecha_aprobacion')
        }),
        ('Totales', {
            'fields': ('total_pagos', 'total_monto'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('id', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [PagoInline]
    
    actions = ['aprobar_planillas']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            num_pagos=Count('pago'),
            suma_monto=Sum('pago__monto_neto')
        )
    
    def total_pagos(self, obj):
        """Total de pagos en la planilla"""
        return obj.num_pagos if hasattr(obj, 'num_pagos') else obj.pago_set.count()
    total_pagos.short_description = "Total Pagos"
    total_pagos.admin_order_field = 'num_pagos'
    
    def total_monto_formatted(self, obj):
        """Total formateado de la planilla"""
        monto = obj.suma_monto if hasattr(obj, 'suma_monto') else obj.total_monto
        return f"S/ {monto:,.2f}" if monto else "S/ 0.00"
    total_monto_formatted.short_description = "Total Monto"
    total_monto_formatted.admin_order_field = 'suma_monto'
    
    def procesada_badge(self, obj):
        """Badge de procesada"""
        color = 'green' if obj.procesada else 'orange'
        text = 'SÍ' if obj.procesada else 'NO'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, text
        )
    procesada_badge.short_description = "Procesada"
    procesada_badge.admin_order_field = 'procesada'
    
    def aprobada_badge(self, obj):
        """Badge de aprobada"""
        color = 'green' if obj.aprobada else 'red'
        text = 'SÍ' if obj.aprobada else 'NO'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, text
        )
    aprobada_badge.short_description = "Aprobada"
    aprobada_badge.admin_order_field = 'aprobada'
    
    def aprobar_planillas(self, request, queryset):
        """Acción para aprobar planillas seleccionadas"""
        planillas_aprobadas = 0
        for planilla in queryset.filter(procesada=True, aprobada=False):
            if planilla.puede_aprobar():
                planilla.aprobar()
                planillas_aprobadas += 1
        
        self.message_user(
            request,
            f"Se aprobaron {planillas_aprobadas} planillas exitosamente."
        )
    aprobar_planillas.short_description = "Aprobar planillas seleccionadas"


@admin.register(Boleta)
class BoletaAdmin(admin.ModelAdmin):
    """Administración de boletas"""
    
    list_display = [
        'pago_info', 'trabajador_info', 'fecha_generacion',
        'tiene_pdf', 'tamaño_archivo'
    ]
    
    list_filter = ['fecha_generacion', 'pago__estado']
    
    search_fields = [
        'pago__trabajador_nombre', 'pago__trabajador_documento'
    ]
    
    readonly_fields = [
        'id', 'fecha_creacion', 'fecha_actualizacion',
        'fecha_generacion', 'tamaño_archivo'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'pago', 'pago__planilla'
        )
    
    def pago_info(self, obj):
        """Información del pago"""
        return f"Pago {obj.pago.id} - {obj.pago.estado}"
    pago_info.short_description = "Pago"
    
    def trabajador_info(self, obj):
        """Información del trabajador"""
        return f"{obj.pago.trabajador_nombre} ({obj.pago.trabajador_documento})"
    trabajador_info.short_description = "Trabajador"
    
    def tiene_pdf(self, obj):
        """Indica si tiene archivo PDF"""
        if obj.archivo_pdf:
            return format_html(
                '<span style="color: green;">✓ SÍ</span>'
            )
        return format_html(
            '<span style="color: red;">✗ NO</span>'
        )
    tiene_pdf.short_description = "PDF"
    
    def tamaño_archivo(self, obj):
        """Tamaño del archivo PDF"""
        if obj.archivo_pdf:
            tamaño = len(obj.archivo_pdf)
            if tamaño > 1024 * 1024:  # MB
                return f"{tamaño / (1024 * 1024):.1f} MB"
            elif tamaño > 1024:  # KB
                return f"{tamaño / 1024:.1f} KB"
            else:
                return f"{tamaño} bytes"
        return "N/A"
    tamaño_archivo.short_description = "Tamaño"


@admin.register(Adelanto)
class AdelantoAdmin(admin.ModelAdmin):
    """Administración de adelantos"""
    
    list_display = [
        'trabajador_nombre', 'trabajador_documento', 'monto_formatted',
        'estado_badge', 'fecha_solicitud', 'fecha_limite_pago'
    ]
    
    list_filter = [
        'estado', 'fecha_solicitud', 'fecha_limite_pago',
        'fecha_aprobacion'
    ]
    
    search_fields = [
        'trabajador_nombre', 'trabajador_documento', 
        'trabajador_id', 'motivo'
    ]
    
    readonly_fields = [
        'id', 'fecha_creacion', 'fecha_actualizacion',
        'fecha_solicitud', 'fecha_aprobacion', 'fecha_pago'
    ]
    
    fieldsets = (
        ('Información del Trabajador', {
            'fields': ('trabajador_id', 'trabajador_nombre', 'trabajador_documento')
        }),
        ('Información del Adelanto', {
            'fields': ('monto', 'motivo', 'observaciones')
        }),
        ('Fechas', {
            'fields': ('fecha_limite_pago', 'fecha_solicitud', 
                      'fecha_aprobacion', 'fecha_pago')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Metadatos', {
            'fields': ('id', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['aprobar_adelantos', 'marcar_como_pagados']
    
    def monto_formatted(self, obj):
        """Monto formateado"""
        return f"S/ {obj.monto:,.2f}"
    monto_formatted.short_description = "Monto"
    monto_formatted.admin_order_field = 'monto'
    
    def estado_badge(self, obj):
        """Badge del estado del adelanto"""
        colors = {
            'PENDIENTE': 'orange',
            'APROBADO': 'green',
            'RECHAZADO': 'red',
            'PAGADO': 'purple'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = "Estado"
    estado_badge.admin_order_field = 'estado'
    
    def aprobar_adelantos(self, request, queryset):
        """Acción para aprobar adelantos seleccionados"""
        adelantos_aprobados = 0
        for adelanto in queryset.filter(estado='PENDIENTE'):
            adelanto.aprobar(request.user)
            adelantos_aprobados += 1
        
        self.message_user(
            request,
            f"Se aprobaron {adelantos_aprobados} adelantos exitosamente."
        )
    aprobar_adelantos.short_description = "Aprobar adelantos seleccionados"
    
    def marcar_como_pagados(self, request, queryset):
        """Acción para marcar adelantos como pagados"""
        adelantos_marcados = 0
        for adelanto in queryset.filter(estado='APROBADO'):
            adelanto.marcar_como_pagado()
            adelantos_marcados += 1
        
        self.message_user(
            request,
            f"Se marcaron como pagados {adelantos_marcados} adelantos."
        )
    marcar_como_pagados.short_description = "Marcar como pagados"


@admin.register(Descuento)
class DescuentoAdmin(admin.ModelAdmin):
    """Administración de descuentos"""
    
    list_display = [
        'nombre', 'tipo_badge', 'valor_formatted', 
        'obligatorio_badge', 'activo_badge'
    ]
    
    list_filter = ['tipo', 'obligatorio', 'activo']
    
    search_fields = ['nombre', 'descripcion']
    
    def tipo_badge(self, obj):
        """Badge del tipo de descuento"""
        color = 'blue' if obj.tipo == 'PORCENTAJE' else 'green'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.tipo
        )
    tipo_badge.short_description = "Tipo"
    tipo_badge.admin_order_field = 'tipo'
    
    def valor_formatted(self, obj):
        """Valor formateado según el tipo"""
        if obj.tipo == 'PORCENTAJE':
            return f"{obj.porcentaje}%"
        else:
            return f"S/ {obj.monto_fijo:,.2f}"
    valor_formatted.short_description = "Valor"
    
    def obligatorio_badge(self, obj):
        """Badge de obligatorio"""
        color = 'red' if obj.obligatorio else 'gray'
        text = 'SÍ' if obj.obligatorio else 'NO'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, text
        )
    obligatorio_badge.short_description = "Obligatorio"
    obligatorio_badge.admin_order_field = 'obligatorio'
    
    def activo_badge(self, obj):
        """Badge de activo"""
        color = 'green' if obj.activo else 'red'
        text = 'SÍ' if obj.activo else 'NO'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, text
        )
    activo_badge.short_description = "Activo"
    activo_badge.admin_order_field = 'activo'


@admin.register(Bonificacion)
class BonificacionAdmin(admin.ModelAdmin):
    """Administración de bonificaciones"""
    
    list_display = [
        'nombre', 'tipo_badge', 'valor_formatted', 
        'imponible_badge', 'activo_badge'
    ]
    
    list_filter = ['tipo', 'imponible', 'activo']
    
    search_fields = ['nombre', 'descripcion']
    
    def tipo_badge(self, obj):
        """Badge del tipo de bonificación"""
        color = 'blue' if obj.tipo == 'PORCENTAJE' else 'green'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.tipo
        )
    tipo_badge.short_description = "Tipo"
    tipo_badge.admin_order_field = 'tipo'
    
    def valor_formatted(self, obj):
        """Valor formateado según el tipo"""
        if obj.tipo == 'PORCENTAJE':
            return f"{obj.porcentaje}%"
        else:
            return f"S/ {obj.monto_fijo:,.2f}"
    valor_formatted.short_description = "Valor"
    
    def imponible_badge(self, obj):
        """Badge de imponible"""
        color = 'blue' if obj.imponible else 'gray'
        text = 'SÍ' if obj.imponible else 'NO'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, text
        )
    imponible_badge.short_description = "Imponible"
    imponible_badge.admin_order_field = 'imponible'
    
    def activo_badge(self, obj):
        """Badge de activo"""
        color = 'green' if obj.activo else 'red'
        text = 'SÍ' if obj.activo else 'NO'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, text
        )
    activo_badge.short_description = "Activo"
    activo_badge.admin_order_field = 'activo'


# Configuración del sitio de admin
admin.site.site_header = "Administración - Sistema de Pagos"
admin.site.site_title = "Pagos Admin"
admin.site.index_title = "Panel de Administración del Sistema de Pagos"
