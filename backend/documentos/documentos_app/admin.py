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
        'codigo_documento', 'titulo', 'tipo', 'estado', 'autor_id',
        'version_actual', 'publico', 'confidencial', 'fecha_creacion',
        'descargas', 'visualizaciones', 'activo'
    ]
    
    list_filter = [
        'tipo', 'estado', 'publico', 'confidencial', 'requiere_aprobacion',
        'fecha_creacion', 'fecha_vigencia', 'fecha_vencimiento', 'activo'
    ]
    
    search_fields = [
        'codigo_documento', 'titulo', 'descripcion', 'autor_id',
        'categoria', 'palabras_clave'
    ]
    
    readonly_fields = [
        'id', 'codigo_documento', 'version_actual', 'tamano_archivo',
        'tipo_mime', 'descargas', 'visualizaciones', 'fecha_creacion',
        'fecha_actualizacion', 'hash_archivo_display'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'titulo', 'descripcion', 'tipo', 'autor_id', 'estado'
            )
        }),
        ('Archivo', {
            'fields': (
                'archivo', 'tamano_archivo', 'tipo_mime'
            )
        }),
        ('Metadatos', {
            'fields': (
                'codigo_documento', 'version_actual', 'categoria',
                'palabras_clave'
            )
        }),
        ('Control de Acceso', {
            'fields': (
                'publico', 'confidencial', 'requiere_aprobacion'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_vigencia', 'fecha_vencimiento', 'fecha_aprobacion'
            )
        }),
        ('Aprobación', {
            'fields': (
                'aprobado_por', 'fecha_aprobacion'
            )
        }),
        ('Estadísticas', {
            'fields': (
                'descargas', 'visualizaciones'
            )
        }),
        ('Sistema', {
            'fields': (
                'id', 'fecha_creacion', 'fecha_actualizacion', 'activo'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activar_documentos', 'desactivar_documentos', 'marcar_publico']
    
    def hash_archivo_display(self, obj):
        """Muestra un hash corto del archivo"""
        if hasattr(obj, 'archivo') and obj.archivo:
            return f"{obj.archivo.name[:50]}..."
        return "No disponible"
    hash_archivo_display.short_description = "Archivo"
    
    def activar_documentos(self, request, queryset):
        """Activa documentos seleccionados"""
        count = queryset.update(activo=True)
        self.message_user(request, f"{count} documentos activados.")
    activar_documentos.short_description = "Activar documentos seleccionados"
    
    def desactivar_documentos(self, request, queryset):
        """Desactiva documentos seleccionados"""
        count = queryset.update(activo=False)
        self.message_user(request, f"{count} documentos desactivados.")
    desactivar_documentos.short_description = "Desactivar documentos seleccionados"
    
    def marcar_publico(self, request, queryset):
        """Marca documentos como públicos"""
        count = queryset.update(publico=True)
        self.message_user(request, f"{count} documentos marcados como públicos.")
    marcar_publico.short_description = "Marcar como públicos"


class VersionDocumentoInline(admin.TabularInline):
    """
    Inline para mostrar versiones en el admin de documentos
    """
    model = VersionDocumento
    extra = 0
    readonly_fields = ['numero_version', 'vigente', 'tamano_archivo', 'fecha_creacion']
    fields = ['numero_version', 'vigente', 'creado_por', 'comentarios', 'tamano_archivo', 'fecha_creacion']


@admin.register(VersionDocumento)
class VersionDocumentoAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo VersionDocumento
    """
    
    list_display = [
        'documento', 'numero_version', 'vigente', 'creado_por',
        'fecha_creacion', 'tamano_archivo_mb', 'activo'
    ]
    
    list_filter = [
        'vigente', 'fecha_creacion', 'activo'
    ]
    
    search_fields = [
        'documento__titulo', 'documento__codigo_documento',
        'creado_por', 'comentarios'
    ]
    
    readonly_fields = [
        'id', 'numero_version', 'tamano_archivo', 'tipo_mime',
        'hash_archivo', 'fecha_creacion', 'fecha_actualizacion'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'documento', 'numero_version', 'vigente'
            )
        }),
        ('Archivo', {
            'fields': (
                'archivo', 'tamano_archivo', 'tipo_mime', 'hash_archivo'
            )
        }),
        ('Metadatos', {
            'fields': (
                'creado_por', 'comentarios'
            )
        }),
        ('Sistema', {
            'fields': (
                'id', 'fecha_creacion', 'fecha_actualizacion', 'activo'
            ),
            'classes': ('collapse',)
        })
    )
    
    def tamano_archivo_mb(self, obj):
        """Muestra el tamaño en MB"""
        if obj.tamano_archivo:
            return f"{obj.tamano_archivo / (1024*1024):.2f} MB"
        return "0 MB"
    tamano_archivo_mb.short_description = "Tamaño (MB)"


@admin.register(SolicitudDocumento)
class SolicitudDocumentoAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo SolicitudDocumento
    """
    
    list_display = [
        'numero_seguimiento', 'titulo', 'tipo', 'estado', 'prioridad',
        'solicitante_id', 'asignado_a', 'fecha_solicitud', 'fecha_limite',
        'esta_vencida_display', 'activo'
    ]
    
    list_filter = [
        'tipo', 'estado', 'prioridad', 'fecha_solicitud',
        'fecha_limite', 'activo'
    ]
    
    search_fields = [
        'numero_seguimiento', 'titulo', 'descripcion',
        'solicitante_id', 'asignado_a'
    ]
    
    readonly_fields = [
        'id', 'numero_seguimiento', 'fecha_solicitud', 'fecha_respuesta',
        'fecha_asignacion', 'fecha_creacion', 'fecha_actualizacion',
        'tiempo_transcurrido_display'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'numero_seguimiento', 'titulo', 'descripcion', 'justificacion'
            )
        }),
        ('Clasificación', {
            'fields': (
                'tipo', 'estado', 'prioridad'
            )
        }),
        ('Asignación', {
            'fields': (
                'solicitante_id', 'asignado_a', 'fecha_asignacion'
            )
        }),
        ('Documento Relacionado', {
            'fields': (
                'documento',
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_solicitud', 'fecha_limite', 'fecha_respuesta'
            )
        }),
        ('Respuesta', {
            'fields': (
                'respuesta', 'respondido_por'
            )
        }),
        ('Archivos', {
            'fields': (
                'archivo_adjunto',
            )
        }),
        ('Sistema', {
            'fields': (
                'id', 'fecha_creacion', 'fecha_actualizacion', 'activo'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['asignar_a_mi', 'marcar_en_proceso', 'marcar_completada']
    
    def esta_vencida_display(self, obj):
        """Muestra si la solicitud está vencida"""
        if obj.esta_vencida():
            return format_html('<span style="color: red;">Vencida</span>')
        return format_html('<span style="color: green;">Vigente</span>')
    esta_vencida_display.short_description = "Estado Fecha"
    
    def tiempo_transcurrido_display(self, obj):
        """Muestra el tiempo transcurrido"""
        horas = obj.tiempo_transcurrido()
        if horas < 24:
            return f"{horas} horas"
        else:
            dias = horas // 24
            return f"{dias} días"
    tiempo_transcurrido_display.short_description = "Tiempo Transcurrido"
    
    def asignar_a_mi(self, request, queryset):
        """Asigna solicitudes al usuario actual"""
        user_id = str(request.user.id) if request.user.id else 'admin'
        count = 0
        for solicitud in queryset:
            solicitud.asignar(user_id)
            count += 1
        self.message_user(request, f"{count} solicitudes asignadas a usted.")
    asignar_a_mi.short_description = "Asignar a mí"
    
    def marcar_en_proceso(self, request, queryset):
        """Marca solicitudes como en proceso"""
        count = queryset.update(estado='EN_PROCESO')
        self.message_user(request, f"{count} solicitudes marcadas en proceso.")
    marcar_en_proceso.short_description = "Marcar en proceso"
    
    def marcar_completada(self, request, queryset):
        """Marca solicitudes como completadas"""
        count = queryset.update(estado='COMPLETADA')
        self.message_user(request, f"{count} solicitudes marcadas como completadas.")
    marcar_completada.short_description = "Marcar completadas"


@admin.register(FlujoDocumento)
class FlujoDocumentoAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo FlujoDocumento
    """
    
    list_display = [
        'documento', 'paso', 'usuario_id', 'fecha_accion',
        'estado_anterior', 'estado_nuevo', 'activo'
    ]
    
    list_filter = [
        'paso', 'estado_anterior', 'estado_nuevo', 'fecha_accion', 'activo'
    ]
    
    search_fields = [
        'documento__titulo', 'documento__codigo_documento',
        'usuario_id', 'detalle'
    ]
    
    readonly_fields = [
        'id', 'fecha_accion', 'fecha_creacion', 'fecha_actualizacion',
        'duracion_segundos'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'documento', 'paso', 'usuario_id', 'detalle'
            )
        }),
        ('Estados', {
            'fields': (
                'estado_anterior', 'estado_nuevo'
            )
        }),
        ('Metadatos', {
            'fields': (
                'fecha_accion', 'duracion_segundos', 'ip_address', 'user_agent'
            )
        }),
        ('Datos Adicionales', {
            'fields': (
                'datos_adicionales',
            )
        }),
        ('Sistema', {
            'fields': (
                'id', 'fecha_creacion', 'fecha_actualizacion', 'activo'
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
