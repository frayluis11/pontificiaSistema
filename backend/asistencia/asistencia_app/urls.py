from django.urls import path
from .views import (
    RegistrarAsistenciaView,
    ActualizarSalidaView, 
    HistorialAsistenciaView,
    MarcarAusenciaView,
    CrearJustificacionView,
    ProcesarJustificacionView,
    JustificacionesDocenteView,
    EstadisticasAsistenciaView,
    CambiarEstrategiaView
)

app_name = 'asistencia_app'

urlpatterns = [
    # Endpoints de Asistencia
    path('registrar/', RegistrarAsistenciaView.as_view(), name='registrar_asistencia'),
    path('actualizar-salida/', ActualizarSalidaView.as_view(), name='actualizar_salida'),
    path('historial/', HistorialAsistenciaView.as_view(), name='historial_asistencia'),
    path('marcar-ausencia/', MarcarAusenciaView.as_view(), name='marcar_ausencia'),
    path('estadisticas/', EstadisticasAsistenciaView.as_view(), name='estadisticas_asistencia'),
    
    # Endpoints de Justificaciones
    path('justificacion/', CrearJustificacionView.as_view(), name='crear_justificacion'),
    path('justificacion/<int:justificacion_id>/procesar/', ProcesarJustificacionView.as_view(), name='procesar_justificacion'),
    path('justificaciones/', JustificacionesDocenteView.as_view(), name='justificaciones_docente'),
    
    # Configuración de estrategias
    path('cambiar-estrategia/', CambiarEstrategiaView.as_view(), name='cambiar_estrategia'),
]
