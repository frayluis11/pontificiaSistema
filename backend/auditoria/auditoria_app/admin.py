"""
Configuración del admin para el microservicio de auditoría
"""

from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
import json

from .models import ActividadSistema


@admin.register(ActividadSistema)
class ActividadSistemaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para ActividadSistema
    """
    
    list_display = [
        'id',
        'fecha_hora',
        'usuario_display',
        'accion_colored',
        'recurso_colored',
        'exito_icon',
        'microservicio',
        'criticidad_colored',
        'duracion_display'
    ]
    
    list_filter = [
        'accion',
        'recurso',
        'microservicio',
        'exito',
        'criticidad',
        'fecha_hora'
    ]
    
    search_fields = [
        'usuario_email',
        'ip_address',
        'detalle',
        'mensaje_error',
        'recurso_id'
    ]
    
    readonly_fields = [
        'id',
        'fecha_hora',
        'detalle_formatted',
        'context_formatted',
        'tags_formatted'
    ]
    
    list_per_page = 50
    date_hierarchy = 'fecha_hora'
    ordering = ['-fecha_hora']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'fecha_hora',
                'usuario_id',
                'usuario_email'
            )
        }),
        ('Actividad', {
            'fields': (
                'accion',
                'recurso',
                'recurso_id',
                'microservicio'
            )
        }),
        ('Resultado', {
            'fields': (
                'exito',
                'codigo_estado',
                'mensaje_error',
                'duracion_ms',
                'criticidad'
            )
        }),
        ('Contexto Técnico', {
            'fields': (
                'ip_address',
                'user_agent',
                'session_id'
            ),
            'classes': ('collapse',)
        }),
        ('Detalles', {
            'fields': (
                'detalle_formatted',
                'context_formatted',
                'tags_formatted'
            ),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """No permitir agregar registros manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir modificar registros"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo admins pueden eliminar registros"""
        return request.user.is_superuser
    
    def usuario_display(self, obj):
        """Mostrar información del usuario"""
        if obj.usuario_email:
            return f"{obj.usuario_email} ({obj.usuario_id})"
        elif obj.usuario_id:
            return f"Usuario ID: {obj.usuario_id}"
        else:
            return "Anónimo"
    usuario_display.short_description = "Usuario"
    
    def accion_colored(self, obj):
        """Mostrar acción con color"""
        color_map = {
            'CREATE': 'green',
            'READ': 'blue',
            'UPDATE': 'orange',
            'DELETE': 'red',
            'LOGIN': 'purple',
            'LOGOUT': 'gray',
            'ERROR': 'red',
            'ACCESS_DENIED': 'red'
        }
        color = color_map.get(obj.accion, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_accion_display()
        )
    accion_colored.short_description = "Acción"
    
    def recurso_colored(self, obj):
        """Mostrar recurso con color"""
        color_map = {
            'USERS': 'blue',
            'DOCUMENTS': 'green',
            'PAYMENTS': 'orange',
            'ATTENDANCE': 'purple',
            'REPORTS': 'brown',
            'AUDIT': 'gray',
            'AUTH': 'red',
            'SYSTEM': 'black'
        }
        color = color_map.get(obj.recurso, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_recurso_display()
        )
    recurso_colored.short_description = "Recurso"
    
    def exito_icon(self, obj):
        """Mostrar icono de éxito/fallo"""
        if obj.exito:
            return format_html(
                '<span style="color: green; font-size: 16px;">✓</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-size: 16px;">✗</span>'
            )
    exito_icon.short_description = "Éxito"
    
    def criticidad_colored(self, obj):
        """Mostrar criticidad con color"""
        if not obj.criticidad:
            return '-'
        
        color_map = {
            'LOW': 'green',
            'MEDIUM': 'orange',  
            'HIGH': 'red',
            'CRITICAL': 'darkred'
        }
        color = color_map.get(obj.criticidad, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_criticidad_display()
        )
    criticidad_colored.short_description = "Criticidad"
    
    def duracion_display(self, obj):
        """Mostrar duración formateada"""
        if not obj.duracion_ms:
            return '-'
        
        if obj.duracion_ms > 1000:
            return f"{obj.duracion_ms / 1000:.2f}s"
        else:
            return f"{obj.duracion_ms}ms"
    duracion_display.short_description = "Duración"
    
    def detalle_formatted(self, obj):
        """Mostrar detalle formateado como JSON"""
        if not obj.detalle:
            return '-'
        
        try:
            formatted = json.dumps(obj.detalle, indent=2, ensure_ascii=False)
            return format_html('<pre style="font-size: 12px;">{}</pre>', formatted)
        except:
            return str(obj.detalle)
    detalle_formatted.short_description = "Detalle"
    
    def context_formatted(self, obj):
        """Mostrar contexto formateado como JSON"""
        if not obj.context:
            return '-'
        
        try:
            formatted = json.dumps(obj.context, indent=2, ensure_ascii=False)
            return format_html('<pre style="font-size: 12px;">{}</pre>', formatted)
        except:
            return str(obj.context)
    context_formatted.short_description = "Contexto"
    
    def tags_formatted(self, obj):
        """Mostrar tags como lista"""
        if not obj.tags:
            return '-'
        
        if isinstance(obj.tags, list):
            tags_html = ''.join([
                f'<span style="background: #007cba; color: white; '
                f'padding: 2px 6px; margin: 2px; border-radius: 3px; '
                f'font-size: 11px;">{tag}</span>'
                for tag in obj.tags
            ])
            return format_html(tags_html)
        else:
            return str(obj.tags)
    tags_formatted.short_description = "Tags"
    
    def get_queryset(self, request):
        """Personalizar queryset"""
        qs = super().get_queryset(request)
        
        # Si no es superuser, solo mostrar logs de los últimos 30 días
        if not request.user.is_superuser:
            hace_30_dias = datetime.now() - timedelta(days=30)
            qs = qs.filter(fecha_hora__gte=hace_30_dias)
        
        return qs
    
    def changelist_view(self, request, extra_context=None):
        """Agregar contexto extra a la vista de lista"""
        extra_context = extra_context or {}
        
        # Estadísticas rápidas
        total_logs = self.get_queryset(request).count()
        logs_hoy = self.get_queryset(request).filter(
            fecha_hora__date=datetime.now().date()
        ).count()
        
        extra_context.update({
            'total_logs': total_logs,
            'logs_hoy': logs_hoy
        })
        
        return super().changelist_view(request, extra_context)


# Personalizar el admin site
admin.site.site_header = "Auditoría - Sistema Pontificia"
admin.site.site_title = "Auditoría Admin"
admin.site.index_title = "Administración de Auditoría"
