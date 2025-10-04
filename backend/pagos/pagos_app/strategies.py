"""
Strategy Pattern para cálculo de descuentos y bonificaciones

Implementa diferentes estrategias para calcular descuentos y bonificaciones
de manera flexible y extensible.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import date

from .models import Descuento, Bonificacion, Pago


class CalculoStrategy(ABC):
    """
    Estrategia base para cálculos de descuentos y bonificaciones
    """
    
    @abstractmethod
    def calcular(self, salario_base: Decimal, **kwargs) -> Decimal:
        """Calcula el monto basado en la estrategia específica"""
        pass
    
    @abstractmethod
    def es_aplicable(self, **kwargs) -> bool:
        """Verifica si la estrategia es aplicable"""
        pass
    
    def validar_monto(self, monto: Decimal) -> Decimal:
        """Valida que el monto no sea negativo"""
        return max(monto, Decimal('0.00'))


class DescuentoStrategy(CalculoStrategy):
    """
    Estrategia base para descuentos
    """
    
    def __init__(self, descuento: Descuento):
        self.descuento = descuento
    
    def es_aplicable(self, fecha: date = None, **kwargs) -> bool:
        """Verifica si el descuento es aplicable"""
        return self.descuento.es_aplicable(fecha)


class PorcentajeDescuentoStrategy(DescuentoStrategy):
    """
    Estrategia para descuentos por porcentaje
    """
    
    def calcular(self, salario_bruto: Decimal, **kwargs) -> Decimal:
        """Calcula descuento por porcentaje"""
        if not self.descuento.porcentaje:
            return Decimal('0.00')
        
        monto = salario_bruto * (self.descuento.porcentaje / 100)
        return self.validar_monto(monto)


class MontoFijoDescuentoStrategy(DescuentoStrategy):
    """
    Estrategia para descuentos de monto fijo
    """
    
    def calcular(self, salario_bruto: Decimal, **kwargs) -> Decimal:
        """Calcula descuento de monto fijo"""
        if not self.descuento.monto_fijo:
            return Decimal('0.00')
        
        return self.validar_monto(self.descuento.monto_fijo)


class EsSaludDescuentoStrategy(DescuentoStrategy):
    """
    Estrategia específica para descuento de EsSalud (9%)
    """
    
    def calcular(self, salario_bruto: Decimal, **kwargs) -> Decimal:
        """Calcula descuento de EsSalud"""
        # EsSalud es 9% del salario bruto
        monto = salario_bruto * Decimal('0.09')
        return self.validar_monto(monto)
    
    def es_aplicable(self, **kwargs) -> bool:
        """EsSalud siempre es aplicable para trabajadores formales"""
        return super().es_aplicable(**kwargs) and self.descuento.tipo == 'ESSALUD'


class ONPDescuentoStrategy(DescuentoStrategy):
    """
    Estrategia específica para descuento de ONP (13%)
    """
    
    def calcular(self, salario_bruto: Decimal, **kwargs) -> Decimal:
        """Calcula descuento de ONP"""
        # ONP es 13% del salario bruto
        monto = salario_bruto * Decimal('0.13')
        return self.validar_monto(monto)
    
    def es_aplicable(self, **kwargs) -> bool:
        """ONP es aplicable según el sistema de pensiones del trabajador"""
        return super().es_aplicable(**kwargs) and self.descuento.tipo == 'ONP'


class AFPDescuentoStrategy(DescuentoStrategy):
    """
    Estrategia específica para descuento de AFP
    """
    
    def calcular(self, salario_bruto: Decimal, **kwargs) -> Decimal:
        """Calcula descuento de AFP"""
        # AFP varía según la AFP específica, usar porcentaje configurado
        if self.descuento.porcentaje:
            monto = salario_bruto * (self.descuento.porcentaje / 100)
        else:
            # Porcentaje promedio de AFP (aproximadamente 12.5%)
            monto = salario_bruto * Decimal('0.125')
        
        return self.validar_monto(monto)
    
    def es_aplicable(self, **kwargs) -> bool:
        """AFP es aplicable según el sistema de pensiones del trabajador"""
        return super().es_aplicable(**kwargs) and self.descuento.tipo == 'AFP'


class QuintaCategoriaDescuentoStrategy(DescuentoStrategy):
    """
    Estrategia para descuento de impuesto de quinta categoría
    """
    
    def calcular(self, salario_bruto: Decimal, **kwargs) -> Decimal:
        """Calcula impuesto de quinta categoría"""
        # Salario anual proyectado
        salario_anual = salario_bruto * 12
        
        # UIT actual (aproximada)
        uit_2024 = Decimal('5150.00')
        
        # Tramos de quinta categoría
        if salario_anual <= uit_2024 * 7:  # Hasta 7 UIT
            return Decimal('0.00')
        elif salario_anual <= uit_2024 * 12:  # De 7 a 12 UIT
            base_imponible = salario_anual - (uit_2024 * 7)
            impuesto_anual = base_imponible * Decimal('0.08')
        elif salario_anual <= uit_2024 * 27:  # De 12 a 27 UIT
            base_imponible = salario_anual - (uit_2024 * 7)
            impuesto_anual = (uit_2024 * 5 * Decimal('0.08')) + \
                           ((base_imponible - uit_2024 * 5) * Decimal('0.14'))
        elif salario_anual <= uit_2024 * 54:  # De 27 a 54 UIT
            base_imponible = salario_anual - (uit_2024 * 7)
            impuesto_anual = (uit_2024 * 5 * Decimal('0.08')) + \
                           (uit_2024 * 15 * Decimal('0.14')) + \
                           ((base_imponible - uit_2024 * 20) * Decimal('0.17'))
        else:  # Más de 54 UIT
            base_imponible = salario_anual - (uit_2024 * 7)
            impuesto_anual = (uit_2024 * 5 * Decimal('0.08')) + \
                           (uit_2024 * 15 * Decimal('0.14')) + \
                           (uit_2024 * 27 * Decimal('0.17')) + \
                           ((base_imponible - uit_2024 * 47) * Decimal('0.20'))
        
        # Impuesto mensual
        impuesto_mensual = impuesto_anual / 12
        return self.validar_monto(impuesto_mensual)
    
    def es_aplicable(self, **kwargs) -> bool:
        """Quinta categoría aplica según el salario"""
        return super().es_aplicable(**kwargs) and self.descuento.tipo == 'QUINTA'


class AdelantoDescuentoStrategy(DescuentoStrategy):
    """
    Estrategia para descuento de adelantos
    """
    
    def calcular(self, salario_bruto: Decimal, monto_adelanto: Decimal = None, **kwargs) -> Decimal:
        """Calcula descuento de adelanto"""
        if not monto_adelanto:
            return Decimal('0.00')
        
        # El descuento no puede ser mayor al salario neto
        return self.validar_monto(monto_adelanto)
    
    def es_aplicable(self, monto_adelanto: Decimal = None, **kwargs) -> bool:
        """Adelanto es aplicable si hay monto especificado"""
        return super().es_aplicable(**kwargs) and monto_adelanto and monto_adelanto > 0


class BonificacionStrategy(CalculoStrategy):
    """
    Estrategia base para bonificaciones
    """
    
    def __init__(self, bonificacion: Bonificacion):
        self.bonificacion = bonificacion
    
    def es_aplicable(self, fecha: date = None, **kwargs) -> bool:
        """Verifica si la bonificación es aplicable"""
        return self.bonificacion.es_aplicable(fecha)


class PorcentajeBonificacionStrategy(BonificacionStrategy):
    """
    Estrategia para bonificaciones por porcentaje
    """
    
    def calcular(self, salario_base: Decimal, **kwargs) -> Decimal:
        """Calcula bonificación por porcentaje"""
        if not self.bonificacion.porcentaje:
            return Decimal('0.00')
        
        monto = salario_base * (self.bonificacion.porcentaje / 100)
        return self.validar_monto(monto)


class MontoFijoBonificacionStrategy(BonificacionStrategy):
    """
    Estrategia para bonificaciones de monto fijo
    """
    
    def calcular(self, salario_base: Decimal, **kwargs) -> Decimal:
        """Calcula bonificación de monto fijo"""
        if not self.bonificacion.monto_fijo:
            return Decimal('0.00')
        
        return self.validar_monto(self.bonificacion.monto_fijo)


class AsignacionFamiliarStrategy(BonificacionStrategy):
    """
    Estrategia para asignación familiar
    """
    
    def calcular(self, salario_base: Decimal, tiene_hijos: bool = False, **kwargs) -> Decimal:
        """Calcula asignación familiar"""
        if not tiene_hijos:
            return Decimal('0.00')
        
        # Asignación familiar en Perú (10% de RMV)
        rmv_2024 = Decimal('1025.00')  # RMV 2024
        asignacion = rmv_2024 * Decimal('0.10')
        
        return self.validar_monto(asignacion)
    
    def es_aplicable(self, tiene_hijos: bool = False, **kwargs) -> bool:
        """Asignación familiar aplica solo si tiene hijos menores"""
        return (super().es_aplicable(**kwargs) and 
                self.bonificacion.tipo == 'ASIG_FAM' and 
                tiene_hijos)


class HorasExtrasBonificacionStrategy(BonificacionStrategy):
    """
    Estrategia para bonificación por horas extras
    """
    
    def calcular(self, salario_base: Decimal, horas_extras: Decimal = 0, **kwargs) -> Decimal:
        """Calcula bonificación por horas extras"""
        if not horas_extras or horas_extras <= 0:
            return Decimal('0.00')
        
        # Valor hora = salario_base / 240 (30 días * 8 horas)
        valor_hora = salario_base / Decimal('240')
        
        # Horas extras se pagan con recargo del 25% las primeras 2 horas
        # y 35% las horas adicionales
        if horas_extras <= 2:
            monto = valor_hora * horas_extras * Decimal('1.25')
        else:
            monto_2_primeras = valor_hora * 2 * Decimal('1.25')
            monto_adicionales = valor_hora * (horas_extras - 2) * Decimal('1.35')
            monto = monto_2_primeras + monto_adicionales
        
        return self.validar_monto(monto)
    
    def es_aplicable(self, horas_extras: Decimal = 0, **kwargs) -> bool:
        """Horas extras aplican si hay horas registradas"""
        return (super().es_aplicable(**kwargs) and 
                self.bonificacion.tipo == 'HORAS_EXTRAS' and 
                horas_extras > 0)


class StrategyFactory:
    """
    Factory para crear estrategias de cálculo
    """
    
    # Mapeo de tipos de descuentos a estrategias
    DESCUENTO_STRATEGIES = {
        'ESSALUD': EsSaludDescuentoStrategy,
        'ONP': ONPDescuentoStrategy,
        'AFP': AFPDescuentoStrategy,
        'QUINTA': QuintaCategoriaDescuentoStrategy,
        'ADELANTO': AdelantoDescuentoStrategy,
        'PRESTAMO': MontoFijoDescuentoStrategy,
        'OTROS': PorcentajeDescuentoStrategy,
    }
    
    # Mapeo de tipos de bonificaciones a estrategias
    BONIFICACION_STRATEGIES = {
        'ASIG_FAM': AsignacionFamiliarStrategy,
        'HORAS_EXTRAS': HorasExtrasBonificacionStrategy,
        'PRODUCTIVIDAD': PorcentajeBonificacionStrategy,
        'GRATIFICACION': MontoFijoBonificacionStrategy,
        'CTS': PorcentajeBonificacionStrategy,
        'VACACIONES': PorcentajeBonificacionStrategy,
        'OTROS': MontoFijoBonificacionStrategy,
    }
    
    @classmethod
    def crear_estrategia_descuento(cls, descuento: Descuento) -> DescuentoStrategy:
        """Crea estrategia de descuento según el tipo"""
        strategy_class = cls.DESCUENTO_STRATEGIES.get(
            descuento.tipo, 
            PorcentajeDescuentoStrategy
        )
        return strategy_class(descuento)
    
    @classmethod
    def crear_estrategia_bonificacion(cls, bonificacion: Bonificacion) -> BonificacionStrategy:
        """Crea estrategia de bonificación según el tipo"""
        strategy_class = cls.BONIFICACION_STRATEGIES.get(
            bonificacion.tipo, 
            MontoFijoBonificacionStrategy
        )
        return strategy_class(bonificacion)


class CalculadoraPagos:
    """
    Clase principal que utiliza las estrategias para calcular pagos
    """
    
    def __init__(self):
        self.factory = StrategyFactory()
    
    def calcular_descuentos(self, pago: Pago, descuentos: List[Descuento], 
                          **kwargs) -> Dict[str, Decimal]:
        """
        Calcula todos los descuentos aplicables a un pago
        """
        descuentos_calculados = {}
        
        for descuento in descuentos:
            strategy = self.factory.crear_estrategia_descuento(descuento)
            
            if strategy.es_aplicable(**kwargs):
                monto = strategy.calcular(pago.monto_bruto, **kwargs)
                descuentos_calculados[descuento.id] = {
                    'descuento': descuento,
                    'monto': monto,
                    'strategy': strategy.__class__.__name__
                }
        
        return descuentos_calculados
    
    def calcular_bonificaciones(self, pago: Pago, bonificaciones: List[Bonificacion], 
                              **kwargs) -> Dict[str, Decimal]:
        """
        Calcula todas las bonificaciones aplicables a un pago
        """
        bonificaciones_calculadas = {}
        
        for bonificacion in bonificaciones:
            strategy = self.factory.crear_estrategia_bonificacion(bonificacion)
            
            if strategy.es_aplicable(**kwargs):
                monto = strategy.calcular(pago.salario_base, **kwargs)
                bonificaciones_calculadas[bonificacion.id] = {
                    'bonificacion': bonificacion,
                    'monto': monto,
                    'strategy': strategy.__class__.__name__
                }
        
        return bonificaciones_calculadas
    
    def calcular_pago_completo(self, pago: Pago, descuentos: List[Descuento], 
                             bonificaciones: List[Bonificacion], **kwargs) -> Dict[str, any]:
        """
        Calcula el pago completo con todos los descuentos y bonificaciones
        """
        # Calcular bonificaciones primero
        bonificaciones_calculadas = self.calcular_bonificaciones(
            pago, bonificaciones, **kwargs
        )
        
        # Sumar bonificaciones al salario base
        total_bonificaciones = sum(
            item['monto'] for item in bonificaciones_calculadas.values()
        )
        pago.total_bonificaciones = total_bonificaciones
        pago.monto_bruto = pago.salario_base + total_bonificaciones
        
        # Calcular descuentos sobre el monto bruto
        descuentos_calculados = self.calcular_descuentos(
            pago, descuentos, **kwargs
        )
        
        # Sumar descuentos
        total_descuentos = sum(
            item['monto'] for item in descuentos_calculados.values()
        )
        pago.total_descuentos = total_descuentos
        
        # Calcular monto neto
        pago.monto_neto = pago.monto_bruto - total_descuentos
        
        # Asegurar que el monto neto no sea negativo
        if pago.monto_neto < 0:
            pago.monto_neto = Decimal('0.00')
        
        return {
            'pago': pago,
            'bonificaciones': bonificaciones_calculadas,
            'descuentos': descuentos_calculados,
            'resumen': {
                'salario_base': pago.salario_base,
                'total_bonificaciones': total_bonificaciones,
                'monto_bruto': pago.monto_bruto,
                'total_descuentos': total_descuentos,
                'monto_neto': pago.monto_neto
            }
        }