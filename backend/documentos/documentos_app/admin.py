"""
Configuración del admin para el servicio de documentos

Define la interfaz administrativa para gestionar documentos,
versiones, solicitudes y flujo de trabajo
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Documento, VersionDocumento, SolicitudDocumento, FlujoDocumento
)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo Documento
    """
    
    list_display = [
        'titulo', 'tipo', 'estado', 'autor', 'created_at', 'updated_at'
    ]
    
    list_filter = [
        'tipo', 'estado', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'titulo', 'autor__username', 'autor__first_name', 'autor__last_name'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'titulo', 'tipo', 'autor', 'estado'
            )
        }),
        ('Archivo', {
            'fields': (
                'archivo',
            )
        }),
        ('Sistema', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    # No definimos acciones personalizadas para mantener simplicidad


class VersionDocumentoInline(admin.TabularInline):
    """
    Inline para mostrar versiones en el admin de documentos
    """
    model = VersionDocumento
    extra = 0
    readonly_fields = ['numero_version', 'created_at']
    fields = ['numero_version', 'vigente', 'created_by', 'comentarios', 'created_at']


@admin.register(VersionDocumento)
class VersionDocumentoAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo VersionDocumento
    """
    
    list_display = [
        'documento', 'numero_version', 'vigente', 'created_by',
        'created_at'
    ]
    
    list_filter = [
        'vigente', 'created_at'
    ]
    
    search_fields = [
        'documento__titulo', 'created_by__username', 'comentarios'
    ]
    
    readonly_fields = [
        'numero_version', 'created_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'documento', 'numero_version', 'vigente'
            )
        }),
        ('Archivo', {
            'fields': (
                'archivo',
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_by', 'comentarios'
            )
        }),
        ('Sistema', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    # Métodos auxiliares removidos para simplicidad


@admin.register(SolicitudDocumento)
class SolicitudDocumentoAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo SolicitudDocumento
    """
    
    list_display = [
        'numero_seguimiento', 'tipo', 'estado', 
        'solicitante', 'fecha_solicitud'
    ]
    
    list_filter = [
        'tipo', 'estado', 'fecha_solicitud'
    ]
    
    search_fields = [
        'numero_seguimiento', 'descripcion',
        'solicitante__username'
    ]
    
    readonly_fields = [
        'numero_seguimiento', 'fecha_solicitud', 'fecha_respuesta'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'numero_seguimiento', 'descripcion'
            )
        }),
        ('Clasificación', {
            'fields': (
                'tipo', 'estado'
            )
        }),
        ('Asignación', {
            'fields': (
                'solicitante',
            )
        }),
        ('Documento Relacionado', {
            'fields': (
                'documento',
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_solicitud', 'fecha_respuesta'
            )
        }),
        ('Respuesta', {
            'fields': (
                'respondido_por',
            )
        })
    )
    
    # Métodos personalizados removidos para simplicidad


@admin.register(FlujoDocumento)
class FlujoDocumentoAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo FlujoDocumento
    """
    
    list_display = [
        'documento', 'paso', 'usuario', 'fecha'
    ]
    
    list_filter = [
        'paso', 'fecha'
    ]
    
    search_fields = [
        'documento__titulo', 'usuario__username', 'detalle'
    ]
    
    readonly_fields = [
        'fecha'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'documento', 'paso', 'usuario', 'detalle'
            )
        }),
        ('Datos Adicionales', {
            'fields': (
                'datos_adicionales',
            )
        }),
        ('Sistema', {
            'fields': (
                'fecha',
            ),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Los registros de flujo no se pueden agregar manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Los registros de flujo no se pueden modificar"""
        return False


# Personalización del sitio admin
admin.site.site_header = "Administración - Servicio de Documentos"
admin.site.site_title = "Documentos Admin"
admin.site.index_title = "Panel de Administración de Documentos"
