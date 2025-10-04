# Simple admin
from django.contrib import admin
from .models import ActividadSistema

@admin.register(ActividadSistema)
class ActividadSistemaAdmin(admin.ModelAdmin):
    list_display = ["id", "fecha", "usuario_email", "accion", "recurso"]
    list_filter = ["accion", "recurso", "nivel_criticidad", "fecha"]
    search_fields = ["usuario_email", "ip_address"]
    readonly_fields = ["id", "fecha"]
    ordering = ["-fecha"]
    list_per_page = 50

