from .models import RegistroHora, JustificacionAusencia
from .repository import AsistenciaRepository
from datetime import datetime, time

class AsistenciaService:
    """Service para lógica de negocio de asistencia"""
    
    def __init__(self):
        self.repository = AsistenciaRepository()
    
    def registrar_asistencia(self, docente_id, aula, seccion, hora_entrada):
        """Registra asistencia con validación de tolerancia"""
        hora_limite = time(8, 5)  # 5 minutos de tolerancia
        estado = 'PUNTUAL' if hora_entrada <= hora_limite else 'TARDANZA'
        
        return self.repository.crear_registro(
            docente_id=docente_id,
            aula=aula,
            seccion=seccion,
            fecha=datetime.now().date(),
            hora_entrada=hora_entrada,
            estado=estado
        )
    
    def validar_tolerancia(self, hora_entrada):
        """Valida tolerancia de 5 minutos"""
        hora_limite = time(8, 5)
        return hora_entrada <= hora_limite
    
    def crear_justificacion(self, docente_id, fecha, motivo):
        """Crea justificación de ausencia"""
        return self.repository.crear_justificacion(
            docente_id=docente_id,
            fecha=fecha,
            motivo=motivo
        )

    def obtener_historial_asistencia(self, docente_id, fecha_inicio=None, fecha_fin=None):
        """Obtiene historial de asistencia de un docente"""
        return self.repository.obtener_registros_por_docente(
            docente_id, fecha_inicio, fecha_fin
        )
