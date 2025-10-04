from .models import RegistroHora, JustificacionAusencia
from .repository import AsistenciaRepository, JustificacionRepository
from .strategies import CalculadorDescuentos
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class AsistenciaService:
    """Service para lógica de negocio de asistencia"""
    
    def __init__(self):
        self.repository = AsistenciaRepository()
        self.calculador_descuentos = CalculadorDescuentos()
    
    def registrar_asistencia(self, docente_id, aula, seccion, hora_entrada=None):
        """
        Registra asistencia con validación completa de tolerancia y cálculo de descuentos
        """
        try:
            with transaction.atomic():
                # Si no se proporciona hora, usar hora actual
                if hora_entrada is None:
                    hora_entrada = timezone.now().time()
                
                fecha_actual = timezone.now().date()
                
                # Verificar si ya existe registro para hoy
                registro_existente = self.repository.obtener_registro_dia(docente_id, fecha_actual)
                if registro_existente:
                    raise ValidationError(f"Ya existe un registro de asistencia para el docente {docente_id} en la fecha {fecha_actual}")
                
                # Validar tolerancia (5 minutos)
                es_puntual = self.validar_tolerancia(hora_entrada)
                minutos_tardanza = self._calcular_minutos_tardanza(hora_entrada)
                
                # Determinar estado
                if es_puntual:
                    estado = 'PUNTUAL'
                    descuento_aplicado = 0.0
                else:
                    estado = 'TARDANZA'
                    # Calcular descuento usando Strategy Pattern
                    descuento_aplicado = self.calculador_descuentos.calcular_descuento(
                        docente_id, minutos_tardanza
                    )
                
                # Crear registro
                registro = self.repository.crear_registro_hora({
                    'docente_id': docente_id,
                    'aula': aula,
                    'seccion': seccion,
                    'fecha': fecha_actual,
                    'hora_entrada': hora_entrada,
                    'estado': estado,
                    'minutos_tardanza': minutos_tardanza,
                    'descuento_aplicado': descuento_aplicado
                })
                
                logger.info(f"Asistencia registrada para docente {docente_id}: {estado} - Descuento: {descuento_aplicado}")
                return registro
                
        except Exception as e:
            logger.error(f"Error al registrar asistencia: {str(e)}")
            raise
    
    def actualizar_salida(self, registro_id, hora_salida=None):
        """Actualiza la hora de salida de un registro"""
        if hora_salida is None:
            hora_salida = timezone.now().time()
        
        return self.repository.actualizar_salida(registro_id, hora_salida)
    
    def validar_tolerancia(self, hora_entrada):
        """Valida tolerancia de 5 minutos (8:05 AM)"""
        hora_limite = time(8, 5)  # 8:05 AM
        return hora_entrada <= hora_limite
    
    def _calcular_minutos_tardanza(self, hora_entrada):
        """Calcula minutos de tardanza respecto a las 8:00 AM"""
        hora_inicio = time(8, 0)  # 8:00 AM
        
        # Convertir a datetime para hacer cálculos
        fecha_base = datetime.now().date()
        dt_entrada = datetime.combine(fecha_base, hora_entrada)
        dt_inicio = datetime.combine(fecha_base, hora_inicio)
        
        if dt_entrada <= dt_inicio:
            return 0
        
        diferencia = dt_entrada - dt_inicio
        return int(diferencia.total_seconds() / 60)
    
    def obtener_historial_docente(self, docente_id, fecha_inicio=None, fecha_fin=None):
        """Obtiene historial completo de asistencia de un docente"""
        return self.repository.obtener_historial_docente(docente_id, fecha_inicio, fecha_fin)
    
    def marcar_ausencia(self, docente_id, fecha, observacion=None):
        """Marca ausencia para un docente en una fecha específica"""
        try:
            with transaction.atomic():
                # Verificar si ya existe registro
                registro_existente = self.repository.obtener_registro_dia(docente_id, fecha)
                if registro_existente:
                    raise ValidationError(f"Ya existe un registro para el docente {docente_id} en la fecha {fecha}")
                
                # Crear registro de ausencia
                registro = self.repository.crear_registro_hora({
                    'docente_id': docente_id,
                    'fecha': fecha,
                    'estado': 'AUSENTE',
                    'observacion': observacion
                })
                
                logger.info(f"Ausencia marcada para docente {docente_id} en fecha {fecha}")
                return registro
                
        except Exception as e:
            logger.error(f"Error al marcar ausencia: {str(e)}")
            raise
    
    def obtener_estadisticas_docente(self, docente_id, fecha_inicio=None, fecha_fin=None):
        """Obtiene estadísticas de asistencia de un docente"""
        return self.repository.obtener_estadisticas_docente(docente_id, fecha_inicio, fecha_fin)
    
    def obtener_tardanzas_periodo(self, docente_id, fecha_inicio, fecha_fin):
        """Obtiene todas las tardanzas de un docente en un período"""
        return self.repository.obtener_tardanzas_periodo(docente_id, fecha_inicio, fecha_fin)
    
    def cambiar_estrategia_descuento(self, tipo_estrategia):
        """Cambia la estrategia de cálculo de descuentos"""
        self.calculador_descuentos.cambiar_estrategia(tipo_estrategia)


class JustificacionService:
    """Service para lógica de negocio de justificaciones"""
    
    def __init__(self):
        self.repository = JustificacionRepository()
        self.asistencia_repository = AsistenciaRepository()
    
    def crear_justificacion(self, docente_id, fecha, motivo, tipo_motivo='OTROS', documentos_adjuntos=None):
        """
        Crea una nueva justificación de ausencia
        """
        try:
            with transaction.atomic():
                # Verificar que existe ausencia o tardanza para justificar
                registro_asistencia = self.asistencia_repository.obtener_registro_dia(docente_id, fecha)
                if not registro_asistencia or registro_asistencia.estado == 'PUNTUAL':
                    raise ValidationError(f"No hay ausencia o tardanza que justificar para el docente {docente_id} en la fecha {fecha}")
                
                # Verificar que no existe justificación previa
                justificacion_existente = self.repository.obtener_justificacion_por_fecha(docente_id, fecha)
                if justificacion_existente:
                    raise ValidationError(f"Ya existe una justificación para el docente {docente_id} en la fecha {fecha}")
                
                # Crear justificación
                justificacion = self.repository.crear_justificacion(
                    docente_id=docente_id,
                    fecha=fecha,
                    motivo=motivo,
                    tipo_motivo=tipo_motivo,
                    documentos_adjuntos=documentos_adjuntos
                )
                
                logger.info(f"Justificación creada para docente {docente_id} en fecha {fecha}")
                return justificacion
                
        except Exception as e:
            logger.error(f"Error al crear justificación: {str(e)}")
            raise
    
    def procesar_justificacion(self, justificacion_id, accion, revisor_id, comentario_revisor=None):
        """
        Procesa una justificación (aprobar o rechazar)
        """
        if accion not in ['APROBAR', 'RECHAZAR']:
            raise ValidationError("Acción debe ser APROBAR o RECHAZAR")
        
        try:
            with transaction.atomic():
                justificacion = self.repository.obtener_por_id(justificacion_id)
                if not justificacion:
                    raise ValidationError(f"Justificación {justificacion_id} no encontrada")
                
                if justificacion.estado != 'PENDIENTE':
                    raise ValidationError(f"La justificación ya fue procesada con estado: {justificacion.estado}")
                
                # Actualizar justificación
                nuevo_estado = 'APROBADA' if accion == 'APROBAR' else 'RECHAZADA'
                justificacion_actualizada = self.repository.actualizar_estado(
                    justificacion_id=justificacion_id,
                    nuevo_estado=nuevo_estado,
                    revisor_id=revisor_id,
                    comentario_revisor=comentario_revisor
                )
                
                # Si se aprueba, actualizar registro de asistencia
                if accion == 'APROBAR':
                    self._actualizar_registro_por_justificacion(justificacion.docente_id, justificacion.fecha)
                
                logger.info(f"Justificación {justificacion_id} {nuevo_estado.lower()} por revisor {revisor_id}")
                return justificacion_actualizada
                
        except Exception as e:
            logger.error(f"Error al procesar justificación: {str(e)}")
            raise
    
    def _actualizar_registro_por_justificacion(self, docente_id, fecha):
        """Actualiza el registro de asistencia cuando se aprueba una justificación"""
        registro = self.asistencia_repository.obtener_registro_dia(docente_id, fecha)
        if registro:
            # Cambiar estado a justificado y eliminar descuento
            self.asistencia_repository.actualizar_estado_registro(
                registro.id, 
                'JUSTIFICADO',
                descuento_aplicado=0.0,
                observacion="Ausencia/tardanza justificada y aprobada"
            )
    
    def obtener_justificaciones_docente(self, docente_id, fecha_inicio=None, fecha_fin=None):
        """Obtiene todas las justificaciones de un docente"""
        return self.repository.obtener_justificaciones_docente(docente_id, fecha_inicio, fecha_fin)
    
    def obtener_justificaciones_pendientes(self):
        """Obtiene todas las justificaciones pendientes de revisión"""
        return self.repository.obtener_por_estado('PENDIENTE')
    
    def obtener_justificacion_detalle(self, justificacion_id):
        """Obtiene el detalle completo de una justificación"""
        return self.repository.obtener_detalle_completo(justificacion_id)
