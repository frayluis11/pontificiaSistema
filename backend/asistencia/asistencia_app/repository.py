"""
Repository para el sistema de asistencia
Sistema Pontificia - Asistencia Service
"""
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet, Q, Count, Avg, Sum
from django.utils import timezone
from datetime import date, datetime, timedelta
from .models import RegistroHora, JustificacionAusencia


class AsistenciaRepository:
    """
    Repository para operaciones de datos del sistema de asistencia
    """
    
    @staticmethod
    def crear_registro_hora(data: Dict[str, Any]) -> RegistroHora:
        """
        Crea un nuevo registro de asistencia
        
        Args:
            data (Dict): Datos del registro
            
        Returns:
            RegistroHora: Registro creado
        """
        return RegistroHora.objects.create(**data)
    
    @staticmethod
    def obtener_registro_por_id(registro_id: int) -> Optional[RegistroHora]:
        """
        Obtiene un registro por su ID
        
        Args:
            registro_id (int): ID del registro
            
        Returns:
            Optional[RegistroHora]: Registro encontrado o None
        """
        try:
            return RegistroHora.objects.get(id=registro_id, activo=True)
        except RegistroHora.DoesNotExist:
            return None
    
    def obtener_registro_dia(self, docente_id, fecha):
        """Obtiene el registro de un docente para una fecha específica"""
        try:
            return RegistroHora.objects.get(
                docente_id=docente_id,
                fecha=fecha,
                activo=True
            )
        except RegistroHora.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_registro_por_docente_fecha_seccion(
        docente_id: int, 
        fecha: date, 
        seccion: str
    ) -> Optional[RegistroHora]:
        """
        Obtiene un registro específico por docente, fecha y sección
        
        Args:
            docente_id (int): ID del docente
            fecha (date): Fecha del registro
            seccion (str): Sección
            
        Returns:
            Optional[RegistroHora]: Registro encontrado o None
        """
        try:
            return RegistroHora.objects.get(
                docente_id=docente_id,
                fecha=fecha,
                seccion=seccion,
                activo=True
            )
        except RegistroHora.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_historial_docente(
        docente_id: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        limit: int = 100
    ) -> QuerySet[RegistroHora]:
        """
        Obtiene el historial de asistencia de un docente
        
        Args:
            docente_id (int): ID del docente
            fecha_inicio (Optional[date]): Fecha inicio del filtro
            fecha_fin (Optional[date]): Fecha fin del filtro
            limit (int): Límite de registros
            
        Returns:
            QuerySet[RegistroHora]: Historial filtrado
        """
        queryset = RegistroHora.objects.filter(
            docente_id=docente_id,
            activo=True
        )
        
        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)
        
        return queryset.order_by('-fecha', '-hora_entrada')[:limit]
    
    @staticmethod
    def obtener_registros_por_fecha(fecha: date) -> QuerySet[RegistroHora]:
        """
        Obtiene todos los registros de una fecha específica
        
        Args:
            fecha (date): Fecha a consultar
            
        Returns:
            QuerySet[RegistroHora]: Registros de la fecha
        """
        return RegistroHora.objects.filter(
            fecha=fecha,
            activo=True
        ).order_by('docente_id', 'seccion')
    
    @staticmethod
    def obtener_tardanzas_periodo(
        fecha_inicio: date,
        fecha_fin: date,
        docente_id: Optional[int] = None
    ) -> QuerySet[RegistroHora]:
        """
        Obtiene registros con tardanzas en un período
        
        Args:
            fecha_inicio (date): Fecha inicio
            fecha_fin (date): Fecha fin
            docente_id (Optional[int]): ID del docente (opcional)
            
        Returns:
            QuerySet[RegistroHora]: Registros con tardanzas
        """
        queryset = RegistroHora.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin],
            estado='TARDANZA',
            activo=True
        )
        
        if docente_id:
            queryset = queryset.filter(docente_id=docente_id)
        
        return queryset.order_by('-fecha')
    
    @staticmethod
    def actualizar_registro(registro_id: int, data: Dict[str, Any]) -> Optional[RegistroHora]:
        """
        Actualiza un registro de asistencia
        
        Args:
            registro_id (int): ID del registro
            data (Dict): Datos a actualizar
            
        Returns:
            Optional[RegistroHora]: Registro actualizado o None
        """
        try:
            registro = RegistroHora.objects.get(id=registro_id, activo=True)
            for field, value in data.items():
                setattr(registro, field, value)
            registro.save()
            return registro
        except RegistroHora.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_estadisticas_docente(
        docente_id: int,
        mes: Optional[int] = None,
        año: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de asistencia de un docente
        
        Args:
            docente_id (int): ID del docente
            mes (Optional[int]): Mes específico
            año (Optional[int]): Año específico
            
        Returns:
            Dict: Estadísticas del docente
        """
        queryset = RegistroHora.objects.filter(
            docente_id=docente_id,
            activo=True
        )
        
        if año:
            queryset = queryset.filter(fecha__year=año)
        if mes:
            queryset = queryset.filter(fecha__month=mes)
        
        stats = queryset.aggregate(
            total_registros=Count('id'),
            total_puntuales=Count('id', filter=Q(estado='PUNTUAL')),
            total_tardanzas=Count('id', filter=Q(estado='TARDANZA')),
            total_faltas=Count('id', filter=Q(estado__in=['AUSENTE', 'FALTA'])),
            total_justificados=Count('id', filter=Q(estado='JUSTIFICADO')),
            promedio_minutos_tardanza=Avg('minutos_tardanza'),
            total_descuentos=Sum('descuento_aplicado')
        )
        
        # Calcular porcentajes
        total = stats['total_registros'] or 1
        stats.update({
            'porcentaje_puntualidad': (stats['total_puntuales'] / total) * 100,
            'porcentaje_tardanzas': (stats['total_tardanzas'] / total) * 100,
            'porcentaje_faltas': (stats['total_faltas'] / total) * 100,
            'porcentaje_justificados': (stats['total_justificados'] / total) * 100
        })
        
        return stats


class JustificacionRepository:
    """
    Repository para operaciones de justificaciones de ausencia
    """
    
    @staticmethod
    def crear_justificacion(data: Dict[str, Any]) -> JustificacionAusencia:
        """
        Crea una nueva justificación de ausencia
        
        Args:
            data (Dict): Datos de la justificación
            
        Returns:
            JustificacionAusencia: Justificación creada
        """
        return JustificacionAusencia.objects.create(**data)
    
    @staticmethod
    def obtener_justificacion_por_fecha(docente_id: int, fecha: date) -> Optional[JustificacionAusencia]:
        """
        Obtiene justificación de un docente para una fecha específica
        
        Args:
            docente_id (int): ID del docente
            fecha (date): Fecha de la justificación
            
        Returns:
            Optional[JustificacionAusencia]: Justificación encontrada o None
        """
        try:
            return JustificacionAusencia.objects.get(
                docente_id=docente_id,
                fecha=fecha,
                activo=True
            )
        except JustificacionAusencia.DoesNotExist:
            return None

    @staticmethod
    def obtener_justificacion_por_id(justificacion_id: int) -> Optional[JustificacionAusencia]:
        """
        Obtiene una justificación por su ID
        
        Args:
            justificacion_id (int): ID de la justificación
            
        Returns:
            Optional[JustificacionAusencia]: Justificación encontrada o None
        """
        try:
            return JustificacionAusencia.objects.get(id=justificacion_id, activo=True)
        except JustificacionAusencia.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_justificaciones_docente(
        docente_id: int,
        estado: Optional[str] = None
    ) -> QuerySet[JustificacionAusencia]:
        """
        Obtiene las justificaciones de un docente
        
        Args:
            docente_id (int): ID del docente
            estado (Optional[str]): Estado específico a filtrar
            
        Returns:
            QuerySet[JustificacionAusencia]: Justificaciones del docente
        """
        queryset = JustificacionAusencia.objects.filter(
            docente_id=docente_id,
            activo=True
        )
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-fecha_creacion')
    
    @staticmethod
    def obtener_justificaciones_pendientes() -> QuerySet[JustificacionAusencia]:
        """
        Obtiene todas las justificaciones pendientes de revisión
        
        Returns:
            QuerySet[JustificacionAusencia]: Justificaciones pendientes
        """
        return JustificacionAusencia.objects.filter(
            estado__in=['PENDIENTE', 'EN_REVISION'],
            activo=True
        ).order_by('fecha_creacion')
    
    @staticmethod
    def obtener_justificaciones_urgentes() -> QuerySet[JustificacionAusencia]:
        """
        Obtiene justificaciones urgentes (más de 3 días sin revisar)
        
        Returns:
            QuerySet[JustificacionAusencia]: Justificaciones urgentes
        """
        hace_tres_dias = timezone.now() - timedelta(days=3)
        return JustificacionAusencia.objects.filter(
            estado='PENDIENTE',
            fecha_creacion__lt=hace_tres_dias,
            activo=True
        ).order_by('fecha_creacion')
    
    @staticmethod
    def actualizar_justificacion(
        justificacion_id: int, 
        data: Dict[str, Any]
    ) -> Optional[JustificacionAusencia]:
        """
        Actualiza una justificación
        
        Args:
            justificacion_id (int): ID de la justificación
            data (Dict): Datos a actualizar
            
        Returns:
            Optional[JustificacionAusencia]: Justificación actualizada o None
        """
        try:
            justificacion = JustificacionAusencia.objects.get(
                id=justificacion_id, 
                activo=True
            )
            for field, value in data.items():
                setattr(justificacion, field, value)
            justificacion.save()
            return justificacion
        except JustificacionAusencia.DoesNotExist:
            return None
    
    @staticmethod
    def existe_justificacion_fecha(docente_id: int, fecha: date) -> bool:
        """
        Verifica si ya existe una justificación para una fecha específica
        
        Args:
            docente_id (int): ID del docente
            fecha (date): Fecha a verificar
            
        Returns:
            bool: True si existe, False si no
        """
        return JustificacionAusencia.objects.filter(
            docente_id=docente_id,
            fecha=fecha,
            activo=True
        ).exists()
    
    @staticmethod
    def obtener_estadisticas_justificaciones() -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de justificaciones
        
        Returns:
            Dict: Estadísticas de justificaciones
        """
        return JustificacionAusencia.objects.filter(activo=True).aggregate(
            total_justificaciones=Count('id'),
            pendientes=Count('id', filter=Q(estado='PENDIENTE')),
            aprobadas=Count('id', filter=Q(estado='APROBADO')),
            rechazadas=Count('id', filter=Q(estado='RECHAZADO')),
            en_revision=Count('id', filter=Q(estado='EN_REVISION'))
        )
