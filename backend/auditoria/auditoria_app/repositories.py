"""
Repository pattern para el microservicio de auditoría
"""

from django.db import models
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging

from .models import ActividadSistema

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Repositorio base con operaciones comunes
    """
    
    def __init__(self, model):
        self.model = model
    
    def get_by_id(self, id: Any):
        """Obtener por ID"""
        try:
            return self.model.objects.get(pk=id)
        except self.model.DoesNotExist:
            return None
    
    def create(self, **data):
        """Crear nueva instancia"""
        return self.model.objects.create(**data)
    
    def update(self, instance, **data):
        """Actualizar instancia"""
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def delete(self, instance):
        """Eliminar instancia"""
        return instance.delete()
    
    def get_all(self):
        """Obtener todos los registros"""
        return self.model.objects.all()
    
    def filter(self, **filters):
        """Filtrar registros"""
        return self.model.objects.filter(**filters)
    
    def count(self, **filters):
        """Contar registros"""
        if filters:
            return self.model.objects.filter(**filters).count()
        return self.model.objects.count()


class AuditoriaRepository(BaseRepository):
    """
    Repository para gestión de actividades de auditoría
    """
    
    def __init__(self):
        super().__init__(ActividadSistema)
    
    def crear_actividad(self, usuario_id: Optional[int] = None, 
                       accion: str = 'OTHER', 
                       recurso: str = 'OTHER', 
                       detalle: Dict = None,
                       **kwargs) -> ActividadSistema:
        """
        Crear nueva actividad de auditoría
        
        Args:
            usuario_id: ID del usuario
            accion: Tipo de acción
            recurso: Recurso afectado
            detalle: Detalles adicionales
            **kwargs: Otros parámetros
        
        Returns:
            ActividadSistema: Nueva actividad creada
        """
        try:
            data = {
                'usuario_id': usuario_id,
                'accion': accion,
                'recurso': recurso,
                'detalle': detalle or {},
                **kwargs
            }
            
            actividad = self.create(**data)
            logger.info(f"Actividad creada: {actividad.id} - {accion} en {recurso}")
            return actividad
            
        except Exception as e:
            logger.error(f"Error al crear actividad: {str(e)}")
            raise
    
    def obtener_por_usuario(self, usuario_id: int, 
                           limite: int = 100) -> models.QuerySet:
        """
        Obtener actividades de un usuario específico
        
        Args:
            usuario_id: ID del usuario
            limite: Límite de resultados
        
        Returns:
            QuerySet con las actividades del usuario
        """
        return self.filter(usuario_id=usuario_id).order_by('-fecha')[:limite]
    
    def obtener_por_fecha_rango(self, fecha_inicio: datetime, 
                               fecha_fin: datetime) -> models.QuerySet:
        """
        Obtener actividades en un rango de fechas
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
        
        Returns:
            QuerySet con las actividades en el rango
        """
        return self.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        ).order_by('-fecha')
    
    def obtener_por_accion(self, accion: str) -> models.QuerySet:
        """
        Obtener actividades por tipo de acción
        
        Args:
            accion: Tipo de acción
        
        Returns:
            QuerySet con las actividades de la acción especificada
        """
        return self.filter(accion=accion).order_by('-fecha')
    
    def obtener_por_recurso(self, recurso: str, 
                           recurso_id: str = None) -> models.QuerySet:
        """
        Obtener actividades por recurso
        
        Args:
            recurso: Tipo de recurso
            recurso_id: ID específico del recurso (opcional)
        
        Returns:
            QuerySet con las actividades del recurso
        """
        filters = {'recurso': recurso}
        if recurso_id:
            filters['recurso_id'] = recurso_id
        
        return self.filter(**filters).order_by('-fecha')
    
    def obtener_actividades_criticas(self, 
                                   fecha_inicio: datetime = None,
                                   fecha_fin: datetime = None) -> models.QuerySet:
        """
        Obtener actividades críticas
        
        Args:
            fecha_inicio: Fecha de inicio (opcional)
            fecha_fin: Fecha de fin (opcional)
        
        Returns:
            QuerySet con actividades críticas
        """
        filters = Q(nivel_criticidad__in=['HIGH', 'CRITICAL']) | Q(exito=False)
        
        if fecha_inicio:
            filters &= Q(fecha__gte=fecha_inicio)
        if fecha_fin:
            filters &= Q(fecha__lte=fecha_fin)
        
        return self.model.objects.filter(filters).order_by('-fecha')
    
    def obtener_intentos_login_fallidos(self, 
                                      fecha_inicio: datetime = None,
                                      limite_horas: int = 24) -> models.QuerySet:
        """
        Obtener intentos de login fallidos
        
        Args:
            fecha_inicio: Fecha de inicio (opcional)
            limite_horas: Últimas X horas a considerar
        
        Returns:
            QuerySet con intentos de login fallidos
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now() - timedelta(hours=limite_horas)
        
        return self.filter(
            accion='LOGIN_FAILED',
            fecha__gte=fecha_inicio
        ).order_by('-fecha')
    
    def buscar_actividades(self, 
                          termino_busqueda: str,
                          campos: List[str] = None) -> models.QuerySet:
        """
        Buscar actividades por término
        
        Args:
            termino_busqueda: Término a buscar
            campos: Campos donde buscar (opcional)
        
        Returns:
            QuerySet con resultados de búsqueda
        """
        if not campos:
            campos = ['usuario_email', 'recurso', 'detalle', 'mensaje_error']
        
        query = Q()
        for campo in campos:
            if campo == 'detalle':
                # Búsqueda en JSON field
                query |= Q(detalle__icontains=termino_busqueda)
            else:
                query |= Q(**{f"{campo}__icontains": termino_busqueda})
        
        return self.model.objects.filter(query).order_by('-fecha')
    
    def obtener_estadisticas_usuario(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtener estadísticas de un usuario
        
        Args:
            usuario_id: ID del usuario
        
        Returns:
            Dict con estadísticas del usuario
        """
        actividades = self.filter(usuario_id=usuario_id)
        
        stats = {
            'total_actividades': actividades.count(),
            'actividades_exitosas': actividades.filter(exito=True).count(),
            'actividades_fallidas': actividades.filter(exito=False).count(),
            'ultima_actividad': None,
            'acciones_mas_frecuentes': [],
            'recursos_mas_accedidos': []
        }
        
        # Última actividad
        ultima = actividades.order_by('-fecha').first()
        if ultima:
            stats['ultima_actividad'] = ultima.fecha
        
        # Acciones más frecuentes
        acciones = actividades.values('accion').annotate(
            count=Count('accion')
        ).order_by('-count')[:5]
        stats['acciones_mas_frecuentes'] = list(acciones)
        
        # Recursos más accedidos
        recursos = actividades.values('recurso').annotate(
            count=Count('recurso')
        ).order_by('-count')[:5]
        stats['recursos_mas_accedidos'] = list(recursos)
        
        return stats
    
    def obtener_estadisticas_sistema(self, 
                                   fecha_inicio: datetime = None,
                                   fecha_fin: datetime = None) -> Dict[str, Any]:
        """
        Obtener estadísticas generales del sistema
        
        Args:
            fecha_inicio: Fecha de inicio (opcional)
            fecha_fin: Fecha de fin (opcional)
        
        Returns:
            Dict con estadísticas del sistema
        """
        filters = {}
        if fecha_inicio:
            filters['fecha__gte'] = fecha_inicio
        if fecha_fin:
            filters['fecha__lte'] = fecha_fin
        
        actividades = self.filter(**filters)
        
        stats = {
            'total_actividades': actividades.count(),
            'actividades_exitosas': actividades.filter(exito=True).count(),
            'actividades_fallidas': actividades.filter(exito=False).count(),
            'usuarios_unicos': actividades.exclude(usuario_id__isnull=True).values('usuario_id').distinct().count(),
            'acciones_por_tipo': {},
            'recursos_por_tipo': {},
            'actividades_por_criticidad': {},
            'actividades_por_microservicio': {},
            'tendencia_diaria': []
        }
        
        # Acciones por tipo
        acciones = actividades.values('accion').annotate(count=Count('accion'))
        stats['acciones_por_tipo'] = {item['accion']: item['count'] for item in acciones}
        
        # Recursos por tipo
        recursos = actividades.values('recurso').annotate(count=Count('recurso'))
        stats['recursos_por_tipo'] = {item['recurso']: item['count'] for item in recursos}
        
        # Actividades por criticidad
        criticidad = actividades.values('nivel_criticidad').annotate(count=Count('nivel_criticidad'))
        stats['actividades_por_criticidad'] = {item['nivel_criticidad']: item['count'] for item in criticidad}
        
        # Actividades por microservicio
        microservicios = actividades.values('microservicio').annotate(count=Count('microservicio'))
        stats['actividades_por_microservicio'] = {item['microservicio']: item['count'] for item in microservicios}
        
        return stats
    
    def obtener_actividades_sospechosas(self, 
                                      horas_analisis: int = 24) -> List[Dict[str, Any]]:
        """
        Detectar actividades sospechosas
        
        Args:
            horas_analisis: Horas hacia atrás para analizar
        
        Returns:
            Lista de actividades sospechosas
        """
        fecha_limite = timezone.now() - timedelta(hours=horas_analisis)
        actividades_sospechosas = []
        
        # 1. Múltiples intentos de login fallidos
        login_fallidos = self.filter(
            accion='LOGIN_FAILED',
            fecha__gte=fecha_limite
        ).values('ip_address').annotate(
            count=Count('ip_address')
        ).filter(count__gte=5)
        
        for item in login_fallidos:
            actividades_sospechosas.append({
                'tipo': 'Múltiples intentos de login fallidos',
                'detalle': f"IP {item['ip_address']} - {item['count']} intentos",
                'criticidad': 'HIGH',
                'ip_address': item['ip_address']
            })
        
        # 2. Accesos denegados frecuentes
        accesos_denegados = self.filter(
            accion='ACCESS_DENIED',
            fecha__gte=fecha_limite
        ).values('usuario_id').annotate(
            count=Count('usuario_id')
        ).filter(count__gte=10)
        
        for item in accesos_denegados:
            actividades_sospechosas.append({
                'tipo': 'Múltiples accesos denegados',
                'detalle': f"Usuario {item['usuario_id']} - {item['count']} intentos",
                'criticidad': 'MEDIUM',
                'usuario_id': item['usuario_id']
            })
        
        # 3. Actividad fuera de horario normal
        actividades_nocturnas = self.filter(
            fecha__gte=fecha_limite,
            fecha__hour__lt=6,  # Entre 00:00 y 06:00
            exito=True
        ).exclude(accion__in=['LOGIN', 'LOGOUT'])
        
        if actividades_nocturnas.count() > 0:
            actividades_sospechosas.append({
                'tipo': 'Actividad fuera de horario',
                'detalle': f"{actividades_nocturnas.count()} actividades entre 00:00-06:00",
                'criticidad': 'MEDIUM'
            })
        
        return actividades_sospechosas
    
    def limpiar_actividades_antiguas(self, dias_retencion: int = 365) -> int:
        """
        Limpiar actividades antiguas según política de retención
        
        Args:
            dias_retencion: Días de retención
        
        Returns:
            Número de actividades eliminadas
        """
        fecha_limite = timezone.now() - timedelta(days=dias_retencion)
        
        # Mantener actividades críticas por más tiempo
        actividades_a_eliminar = self.filter(
            fecha__lt=fecha_limite,
            nivel_criticidad='LOW'
        )
        
        count = actividades_a_eliminar.count()
        actividades_a_eliminar.delete()
        
        logger.info(f"Limpiadas {count} actividades antiguas")
        return count
    
    def obtener_filtros_avanzados(self, 
                                 usuario_id: int = None,
                                 acciones: List[str] = None,
                                 recursos: List[str] = None,
                                 fecha_inicio: datetime = None,
                                 fecha_fin: datetime = None,
                                 nivel_criticidad: List[str] = None,
                                 exito: bool = None,
                                 ip_address: str = None,
                                 microservicio: str = None) -> models.QuerySet:
        """
        Obtener actividades con filtros avanzados
        
        Args:
            usuario_id: ID del usuario
            acciones: Lista de acciones
            recursos: Lista de recursos
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            nivel_criticidad: Lista de niveles de criticidad
            exito: Filtro por éxito
            ip_address: Dirección IP
            microservicio: Microservicio
        
        Returns:
            QuerySet filtrado
        """
        filters = Q()
        
        if usuario_id:
            filters &= Q(usuario_id=usuario_id)
        
        if acciones:
            filters &= Q(accion__in=acciones)
        
        if recursos:
            filters &= Q(recurso__in=recursos)
        
        if fecha_inicio:
            filters &= Q(fecha__gte=fecha_inicio)
        
        if fecha_fin:
            filters &= Q(fecha__lte=fecha_fin)
        
        if nivel_criticidad:
            filters &= Q(nivel_criticidad__in=nivel_criticidad)
        
        if exito is not None:
            filters &= Q(exito=exito)
        
        if ip_address:
            filters &= Q(ip_address=ip_address)
        
        if microservicio:
            filters &= Q(microservicio=microservicio)
        
        return self.model.objects.filter(filters).order_by('-fecha')
    
    def obtener_metricas_rendimiento(self) -> Dict[str, Any]:
        """
        Obtener métricas de rendimiento del sistema
        
        Returns:
            Dict con métricas de rendimiento
        """
        # Actividades con duración registrada
        actividades_con_duracion = self.filter(duracion_ms__isnull=False)
        
        if not actividades_con_duracion.exists():
            return {'message': 'No hay datos de duración disponibles'}
        
        metricas = actividades_con_duracion.aggregate(
            duracion_promedio=Avg('duracion_ms'),
            duracion_minima=Min('duracion_ms'),
            duracion_maxima=Max('duracion_ms')
        )
        
        # Operaciones más lentas
        operaciones_lentas = actividades_con_duracion.order_by('-duracion_ms')[:10]
        
        metricas['operaciones_mas_lentas'] = [
            {
                'accion': act.accion,
                'recurso': act.recurso,
                'duracion_ms': act.duracion_ms,
                'fecha': act.fecha
            }
            for act in operaciones_lentas
        ]
        
        return metricas
    
    def obtener_actividades_filtradas(self, filtros: Dict = None):
        """
        Obtener actividades filtradas para exportación
        """
        if not filtros:
            return self.get_all().order_by('-fecha')
        
        return self.buscar_actividades(
            usuario_id=filtros.get('usuario_id'),
            accion=filtros.get('accion'),
            recurso=filtros.get('recurso'),
            fecha_inicio=filtros.get('fecha_inicio'),
            fecha_fin=filtros.get('fecha_fin'),
            nivel_criticidad=filtros.get('nivel_criticidad'),
            ip_address=filtros.get('ip_address')
        )