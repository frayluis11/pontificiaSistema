"""
Repositories para el microservicio de pagos

Implementa el patrón Repository para abstraer el acceso a datos
y centralizar las consultas complejas a la base de datos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from django.db.models import Q, Sum, Count, Avg
from django.db.models.query import QuerySet
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from .models import (
    Pago, Planilla, Boleta, Adelanto, Descuento, 
    Bonificacion, PagoDescuento, PagoBonificacion
)


class BaseRepository(ABC):
    """
    Repositorio base con operaciones CRUD comunes
    """
    
    def __init__(self, model):
        self.model = model
    
    def create(self, **kwargs):
        """Crea una nueva instancia"""
        return self.model.objects.create(**kwargs)
    
    def get_by_id(self, id: str):
        """Obtiene por ID"""
        try:
            return self.model.objects.get(id=id, activo=True)
        except self.model.DoesNotExist:
            return None
    
    def get_all(self) -> QuerySet:
        """Obtiene todos los registros activos"""
        return self.model.objects.filter(activo=True)
    
    def update(self, id: str, **kwargs):
        """Actualiza un registro"""
        obj = self.get_by_id(id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            obj.save()
            return obj
        return None
    
    def delete(self, id: str):
        """Eliminación lógica"""
        obj = self.get_by_id(id)
        if obj:
            obj.activo = False
            obj.save()
            return True
        return False
    
    def filter(self, **kwargs) -> QuerySet:
        """Filtrado genérico"""
        return self.model.objects.filter(activo=True, **kwargs)


class PagoRepository(BaseRepository):
    """
    Repositorio específico para pagos
    """
    
    def __init__(self):
        super().__init__(Pago)
    
    def buscar_por_trabajador(self, trabajador_id: str) -> QuerySet:
        """Busca pagos por ID de trabajador"""
        return self.filter(trabajador_id=trabajador_id).order_by('-fecha_calculo')
    
    def buscar_por_planilla(self, planilla_id: str) -> QuerySet:
        """Busca pagos por planilla"""
        return self.filter(planilla_id=planilla_id).order_by('trabajador_nombre')
    
    def buscar_por_periodo(self, año: int, mes: int) -> QuerySet:
        """Busca pagos por periodo"""
        return self.filter(
            planilla__año=año,
            planilla__mes=mes
        ).select_related('planilla')
    
    def buscar_por_documento(self, documento: str) -> QuerySet:
        """Busca pagos por documento del trabajador"""
        return self.filter(trabajador_documento__icontains=documento)
    
    def buscar_por_nombre(self, nombre: str) -> QuerySet:
        """Busca pagos por nombre del trabajador"""
        return self.filter(trabajador_nombre__icontains=nombre)
    
    def obtener_con_boleta(self) -> QuerySet:
        """Obtiene pagos que ya tienen boleta generada"""
        return self.filter(boleta__isnull=False).select_related('boleta')
    
    def obtener_sin_boleta(self) -> QuerySet:
        """Obtiene pagos que no tienen boleta generada"""
        return self.filter(boleta__isnull=True)
    
    def obtener_por_estado(self, estado: str) -> QuerySet:
        """Obtiene pagos por estado"""
        return self.filter(estado=estado)
    
    def obtener_aprobados(self) -> QuerySet:
        """Obtiene pagos aprobados"""
        return self.obtener_por_estado('APROBADO')
    
    def obtener_pagados(self) -> QuerySet:
        """Obtiene pagos ya pagados"""
        return self.obtener_por_estado('PAGADO')
    
    def calcular_total_por_trabajador(self, trabajador_id: str, año: int = None) -> Dict[str, Decimal]:
        """Calcula totales de pagos por trabajador"""
        queryset = self.buscar_por_trabajador(trabajador_id)
        
        if año:
            queryset = queryset.filter(planilla__año=año)
        
        return queryset.aggregate(
            total_bruto=Sum('monto_bruto') or Decimal('0.00'),
            total_descuentos=Sum('total_descuentos') or Decimal('0.00'),
            total_bonificaciones=Sum('total_bonificaciones') or Decimal('0.00'),
            total_neto=Sum('monto_neto') or Decimal('0.00'),
            cantidad_pagos=Count('id')
        )
    
    def obtener_estadisticas_mensuales(self, año: int, mes: int) -> Dict[str, Any]:
        """Obtiene estadísticas de pagos del mes"""
        pagos = self.buscar_por_periodo(año, mes)
        
        return {
            'total_trabajadores': pagos.count(),
            'total_bruto': pagos.aggregate(Sum('monto_bruto'))['monto_bruto__sum'] or Decimal('0.00'),
            'total_descuentos': pagos.aggregate(Sum('total_descuentos'))['total_descuentos__sum'] or Decimal('0.00'),
            'total_bonificaciones': pagos.aggregate(Sum('total_bonificaciones'))['total_bonificaciones__sum'] or Decimal('0.00'),
            'total_neto': pagos.aggregate(Sum('monto_neto'))['monto_neto__sum'] or Decimal('0.00'),
            'promedio_salario': pagos.aggregate(Avg('monto_neto'))['monto_neto__avg'] or Decimal('0.00'),
            'pagos_por_estado': pagos.values('estado').annotate(cantidad=Count('id')),
        }
    
    def buscar_por_rango_fechas(self, fecha_inicio: date, fecha_fin: date) -> QuerySet:
        """Busca pagos en un rango de fechas"""
        return self.filter(
            fecha_calculo__date__gte=fecha_inicio,
            fecha_calculo__date__lte=fecha_fin
        )
    
    def obtener_con_descuentos_bonificaciones(self) -> QuerySet:
        """Obtiene pagos con sus descuentos y bonificaciones"""
        return self.get_all().prefetch_related(
            'pagodescuento_set__descuento',
            'pagobonificacion_set__bonificacion'
        )


class PlanillaRepository(BaseRepository):
    """
    Repositorio específico para planillas
    """
    
    def __init__(self):
        super().__init__(Planilla)
    
    def buscar_por_periodo(self, año: int, mes: int) -> Optional[Planilla]:
        """Busca planilla por periodo específico"""
        try:
            return self.model.objects.get(año=año, mes=mes, activo=True)
        except self.model.DoesNotExist:
            return None
    
    def buscar_por_año(self, año: int) -> QuerySet:
        """Busca planillas por año"""
        return self.filter(año=año).order_by('mes')
    
    def obtener_procesadas(self) -> QuerySet:
        """Obtiene planillas procesadas"""
        return self.filter(procesada=True)
    
    def obtener_aprobadas(self) -> QuerySet:
        """Obtiene planillas aprobadas"""
        return self.filter(aprobada=True)
    
    def obtener_pendientes_aprobacion(self) -> QuerySet:
        """Obtiene planillas procesadas pero no aprobadas"""
        return self.filter(procesada=True, aprobada=False)
    
    def crear_planilla_periodo(self, año: int, mes: int, periodo_inicio: date, periodo_fin: date) -> Planilla:
        """Crea una nueva planilla para un periodo"""
        return self.create(
            año=año,
            mes=mes,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin
        )
    
    def obtener_estadisticas_anuales(self, año: int) -> Dict[str, Any]:
        """Obtiene estadísticas anuales de planillas"""
        planillas = self.buscar_por_año(año)
        
        return {
            'total_planillas': planillas.count(),
            'planillas_procesadas': planillas.filter(procesada=True).count(),
            'planillas_aprobadas': planillas.filter(aprobada=True).count(),
            'total_bruto_anual': planillas.aggregate(Sum('total_bruto'))['total_bruto__sum'] or Decimal('0.00'),
            'total_neto_anual': planillas.aggregate(Sum('total_neto'))['total_neto__sum'] or Decimal('0.00'),
            'promedio_trabajadores': planillas.aggregate(Avg('cantidad_trabajadores'))['cantidad_trabajadores__avg'] or 0,
        }


class BoletaRepository(BaseRepository):
    """
    Repositorio específico para boletas
    """
    
    def __init__(self):
        super().__init__(Boleta)
    
    def buscar_por_pago(self, pago_id: str) -> Optional[Boleta]:
        """Busca boleta por pago"""
        try:
            return self.model.objects.get(pago_id=pago_id, activo=True)
        except self.model.DoesNotExist:
            return None
    
    def buscar_por_numero(self, numero_boleta: str) -> Optional[Boleta]:
        """Busca boleta por número"""
        try:
            return self.model.objects.get(numero_boleta=numero_boleta, activo=True)
        except self.model.DoesNotExist:
            return None
    
    def buscar_por_trabajador(self, trabajador_id: str) -> QuerySet:
        """Busca boletas por trabajador"""
        return self.filter(pago__trabajador_id=trabajador_id).select_related('pago')
    
    def buscar_por_periodo(self, año: int, mes: int) -> QuerySet:
        """Busca boletas por periodo"""
        return self.filter(
            pago__planilla__año=año,
            pago__planilla__mes=mes
        ).select_related('pago__planilla')
    
    def obtener_enviadas_por_email(self) -> QuerySet:
        """Obtiene boletas enviadas por email"""
        return self.filter(enviada_por_email=True)
    
    def obtener_pendientes_envio(self) -> QuerySet:
        """Obtiene boletas pendientes de envío"""
        return self.filter(enviada_por_email=False)
    
    def obtener_con_archivo(self) -> QuerySet:
        """Obtiene boletas que tienen archivo PDF"""
        return self.filter(archivo_pdf__isnull=False)
    
    def obtener_sin_archivo(self) -> QuerySet:
        """Obtiene boletas sin archivo PDF"""
        return self.filter(archivo_pdf__isnull=True)


class AdelantoRepository(BaseRepository):
    """
    Repositorio específico para adelantos
    """
    
    def __init__(self):
        super().__init__(Adelanto)
    
    def buscar_por_trabajador(self, trabajador_id: str) -> QuerySet:
        """Busca adelantos por trabajador"""
        return self.filter(trabajador_id=trabajador_id).order_by('-fecha_solicitud')
    
    def buscar_por_estado(self, estado: str) -> QuerySet:
        """Busca adelantos por estado"""
        return self.filter(estado=estado)
    
    def obtener_solicitados(self) -> QuerySet:
        """Obtiene adelantos solicitados (pendientes)"""
        return self.buscar_por_estado('SOLICITADO')
    
    def obtener_aprobados(self) -> QuerySet:
        """Obtiene adelantos aprobados"""
        return self.buscar_por_estado('APROBADO')
    
    def obtener_descontados(self) -> QuerySet:
        """Obtiene adelantos ya descontados"""
        return self.buscar_por_estado('DESCONTADO')
    
    def obtener_rechazados(self) -> QuerySet:
        """Obtiene adelantos rechazados"""
        return self.buscar_por_estado('RECHAZADO')
    
    def buscar_por_rango_fechas(self, fecha_inicio: date, fecha_fin: date) -> QuerySet:
        """Busca adelantos en un rango de fechas"""
        return self.filter(
            fecha_solicitud__date__gte=fecha_inicio,
            fecha_solicitud__date__lte=fecha_fin
        )
    
    def obtener_pendientes_descuento(self) -> QuerySet:
        """Obtiene adelantos aprobados pendientes de descuento"""
        return self.filter(
            estado='APROBADO',
            pago_descuento__isnull=True
        )
    
    def calcular_total_por_trabajador(self, trabajador_id: str, año: int = None) -> Dict[str, Decimal]:
        """Calcula totales de adelantos por trabajador"""
        queryset = self.buscar_por_trabajador(trabajador_id)
        
        if año:
            queryset = queryset.filter(fecha_solicitud__year=año)
        
        return {
            'total_solicitado': queryset.aggregate(Sum('monto_solicitado'))['monto_solicitado__sum'] or Decimal('0.00'),
            'total_aprobado': queryset.filter(estado__in=['APROBADO', 'DESCONTADO']).aggregate(
                Sum('monto_aprobado'))['monto_aprobado__sum'] or Decimal('0.00'),
            'cantidad_adelantos': queryset.count(),
            'adelantos_pendientes': queryset.filter(estado='SOLICITADO').count(),
        }


class DescuentoRepository(BaseRepository):
    """
    Repositorio específico para descuentos
    """
    
    def __init__(self):
        super().__init__(Descuento)
    
    def buscar_por_tipo(self, tipo: str) -> QuerySet:
        """Busca descuentos por tipo"""
        return self.filter(tipo=tipo)
    
    def obtener_obligatorios(self) -> QuerySet:
        """Obtiene descuentos obligatorios"""
        return self.filter(obligatorio=True)
    
    def obtener_aplicables(self, fecha: date = None) -> QuerySet:
        """Obtiene descuentos aplicables en una fecha"""
        if fecha is None:
            fecha = date.today()
        
        return self.filter(
            aplicable_desde__lte=fecha
        ).filter(
            Q(aplicable_hasta__isnull=True) | Q(aplicable_hasta__gte=fecha)
        )
    
    def buscar_por_nombre(self, nombre: str) -> QuerySet:
        """Busca descuentos por nombre"""
        return self.filter(nombre__icontains=nombre)


class BonificacionRepository(BaseRepository):
    """
    Repositorio específico para bonificaciones
    """
    
    def __init__(self):
        super().__init__(Bonificacion)
    
    def buscar_por_tipo(self, tipo: str) -> QuerySet:
        """Busca bonificaciones por tipo"""
        return self.filter(tipo=tipo)
    
    def obtener_que_requieren_aprobacion(self) -> QuerySet:
        """Obtiene bonificaciones que requieren aprobación"""
        return self.filter(requiere_aprobacion=True)
    
    def obtener_aplicables(self, fecha: date = None) -> QuerySet:
        """Obtiene bonificaciones aplicables en una fecha"""
        if fecha is None:
            fecha = date.today()
        
        return self.filter(
            aplicable_desde__lte=fecha
        ).filter(
            Q(aplicable_hasta__isnull=True) | Q(aplicable_hasta__gte=fecha)
        )
    
    def buscar_por_nombre(self, nombre: str) -> QuerySet:
        """Busca bonificaciones por nombre"""
        return self.filter(nombre__icontains=nombre)


class PagoDescuentoRepository(BaseRepository):
    """
    Repositorio para relaciones pago-descuento
    """
    
    def __init__(self):
        super().__init__(PagoDescuento)
    
    def buscar_por_pago(self, pago_id: str) -> QuerySet:
        """Busca descuentos de un pago"""
        return self.filter(pago_id=pago_id).select_related('descuento')
    
    def buscar_por_descuento(self, descuento_id: str) -> QuerySet:
        """Busca pagos que tienen un descuento específico"""
        return self.filter(descuento_id=descuento_id).select_related('pago')


class PagoBonificacionRepository(BaseRepository):
    """
    Repositorio para relaciones pago-bonificación
    """
    
    def __init__(self):
        super().__init__(PagoBonificacion)
    
    def buscar_por_pago(self, pago_id: str) -> QuerySet:
        """Busca bonificaciones de un pago"""
        return self.filter(pago_id=pago_id).select_related('bonificacion')
    
    def buscar_por_bonificacion(self, bonificacion_id: str) -> QuerySet:
        """Busca pagos que tienen una bonificación específica"""
        return self.filter(bonificacion_id=bonificacion_id).select_related('pago')


# Clase principal que agrupa todos los repositorios
class PagosRepositoryManager:
    """
    Manager que agrupa todos los repositorios para facilitar el acceso
    """
    
    def __init__(self):
        self.pagos = PagoRepository()
        self.planillas = PlanillaRepository()
        self.boletas = BoletaRepository()
        self.adelantos = AdelantoRepository()
        self.descuentos = DescuentoRepository()
        self.bonificaciones = BonificacionRepository()
        self.pago_descuentos = PagoDescuentoRepository()
        self.pago_bonificaciones = PagoBonificacionRepository()
    
    def busqueda_global(self, termino: str) -> Dict[str, QuerySet]:
        """
        Realiza búsqueda global en todos los repositorios
        """
        return {
            'pagos': self.pagos.filter(
                Q(trabajador_nombre__icontains=termino) |
                Q(trabajador_documento__icontains=termino)
            ),
            'planillas': self.planillas.filter(nombre__icontains=termino),
            'boletas': self.boletas.filter(numero_boleta__icontains=termino),
            'adelantos': self.adelantos.filter(
                Q(trabajador_nombre__icontains=termino) |
                Q(motivo__icontains=termino)
            ),
            'descuentos': self.descuentos.buscar_por_nombre(termino),
            'bonificaciones': self.bonificaciones.buscar_por_nombre(termino),
        }