"""
Strategy Pattern para calcular descuentos por tardanza
Sistema Pontificia - Asistencia Service
"""
from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class DescuentoStrategy(ABC):
    """
    Estrategia abstracta para calcular descuentos por tardanza
    """
    
    @abstractmethod
    def calcular_descuento(self, minutos_tardanza: int, salario_hora: Decimal) -> Decimal:
        """
        Calcula el descuento basado en los minutos de tardanza
        
        Args:
            minutos_tardanza (int): Minutos de tardanza
            salario_hora (Decimal): Salario por hora del docente
            
        Returns:
            Decimal: Monto del descuento
        """
        pass
    
    @abstractmethod
    def get_descripcion(self) -> str:
        """
        Retorna la descripción de la estrategia
        
        Returns:
            str: Descripción de la estrategia
        """
        pass


class DescuentoLinealStrategy(DescuentoStrategy):
    """
    Estrategia de descuento lineal: descuento proporcional a los minutos de tardanza
    """
    
    def calcular_descuento(self, minutos_tardanza: int, salario_hora: Decimal) -> Decimal:
        """
        Descuento lineal: cada minuto de tardanza descuenta proporcionalmente
        
        Args:
            minutos_tardanza (int): Minutos de tardanza
            salario_hora (Decimal): Salario por hora
            
        Returns:
            Decimal: Descuento calculado
        """
        if minutos_tardanza <= 5:  # Tolerancia de 5 minutos
            return Decimal('0.00')
        
        minutos_descontables = minutos_tardanza - 5
        descuento_por_minuto = salario_hora / 60
        descuento = descuento_por_minuto * minutos_descontables
        
        return descuento.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_descripcion(self) -> str:
        return "Descuento lineal por minuto de tardanza (tolerancia 5 min)"


class DescuentoEscalonadoStrategy(DescuentoStrategy):
    """
    Estrategia de descuento escalonado: diferentes tasas según rangos de tardanza
    """
    
    def calcular_descuento(self, minutos_tardanza: int, salario_hora: Decimal) -> Decimal:
        """
        Descuento escalonado con diferentes tarifas por rango:
        - 0-5 min: Sin descuento (tolerancia)
        - 6-15 min: Descuento del 10% del salario hora
        - 16-30 min: Descuento del 25% del salario hora
        - 31-60 min: Descuento del 50% del salario hora
        - Más de 60 min: Descuento del 100% del salario hora
        
        Args:
            minutos_tardanza (int): Minutos de tardanza
            salario_hora (Decimal): Salario por hora
            
        Returns:
            Decimal: Descuento calculado
        """
        if minutos_tardanza <= 5:
            return Decimal('0.00')
        elif minutos_tardanza <= 15:
            descuento = salario_hora * Decimal('0.10')
        elif minutos_tardanza <= 30:
            descuento = salario_hora * Decimal('0.25')
        elif minutos_tardanza <= 60:
            descuento = salario_hora * Decimal('0.50')
        else:
            descuento = salario_hora * Decimal('1.00')
        
        return descuento.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_descripcion(self) -> str:
        return "Descuento escalonado por rangos de tardanza"


class DescuentoProgresivStrategy(DescuentoStrategy):
    """
    Estrategia de descuento progresivo: aumenta exponencialmente con la tardanza
    """
    
    def calcular_descuento(self, minutos_tardanza: int, salario_hora: Decimal) -> Decimal:
        """
        Descuento progresivo que aumenta exponencialmente:
        - Factor de multiplicación crece con los minutos de tardanza
        
        Args:
            minutos_tardanza (int): Minutos de tardanza
            salario_hora (Decimal): Salario por hora
            
        Returns:
            Decimal: Descuento calculado
        """
        if minutos_tardanza <= 5:
            return Decimal('0.00')
        
        minutos_descontables = minutos_tardanza - 5
        
        # Factor progresivo: empieza en 0.02 y aumenta exponencialmente
        if minutos_descontables <= 10:
            factor = Decimal('0.02') * minutos_descontables
        elif minutos_descontables <= 30:
            factor = Decimal('0.20') + (Decimal('0.03') * (minutos_descontables - 10))
        else:
            factor = Decimal('0.80') + (Decimal('0.01') * (minutos_descontables - 30))
        
        # Limitar al 100% del salario hora
        factor = min(factor, Decimal('1.00'))
        descuento = salario_hora * factor
        
        return descuento.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_descripcion(self) -> str:
        return "Descuento progresivo exponencial"


class DescuentoSemanalStrategy(DescuentoStrategy):
    """
    Estrategia que considera el historial semanal de tardanzas
    """
    
    def __init__(self, tardanzas_semana: int = 0):
        """
        Inicializa la estrategia con el historial semanal
        
        Args:
            tardanzas_semana (int): Número de tardanzas en la semana
        """
        self.tardanzas_semana = tardanzas_semana
    
    def calcular_descuento(self, minutos_tardanza: int, salario_hora: Decimal) -> Decimal:
        """
        Descuento que considera el historial semanal:
        - Multiplicador basado en tardanzas acumuladas en la semana
        
        Args:
            minutos_tardanza (int): Minutos de tardanza
            salario_hora (Decimal): Salario por hora
            
        Returns:
            Decimal: Descuento calculado
        """
        if minutos_tardanza <= 5:
            return Decimal('0.00')
        
        # Descuento base lineal
        minutos_descontables = minutos_tardanza - 5
        descuento_base = (salario_hora / 60) * minutos_descontables
        
        # Multiplicador por historial semanal
        if self.tardanzas_semana <= 1:
            multiplicador = Decimal('1.0')
        elif self.tardanzas_semana <= 3:
            multiplicador = Decimal('1.5')
        elif self.tardanzas_semana <= 5:
            multiplicador = Decimal('2.0')
        else:
            multiplicador = Decimal('3.0')
        
        descuento = descuento_base * multiplicador
        
        # Limitar al salario hora completo
        descuento = min(descuento, salario_hora)
        
        return descuento.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_descripcion(self) -> str:
        return f"Descuento con historial semanal ({self.tardanzas_semana} tardanzas previas)"


class CalculadorDescuentos:
    """
    Context class que utiliza las diferentes estrategias de descuento
    """
    
    # Estrategias disponibles
    ESTRATEGIAS = {
        'lineal': DescuentoLinealStrategy,
        'escalonado': DescuentoEscalonadoStrategy,
        'progresivo': DescuentoProgresivStrategy,
        'semanal': DescuentoSemanalStrategy
    }
    
    def __init__(self, estrategia: str = 'escalonado', **kwargs):
        """
        Inicializa el calculador con una estrategia específica
        
        Args:
            estrategia (str): Nombre de la estrategia a usar
            **kwargs: Argumentos adicionales para la estrategia
        """
        if estrategia not in self.ESTRATEGIAS:
            raise ValueError(f"Estrategia '{estrategia}' no válida. Opciones: {list(self.ESTRATEGIAS.keys())}")
        
        strategy_class = self.ESTRATEGIAS[estrategia]
        
        # Inicializar con argumentos si es necesario
        if estrategia == 'semanal':
            self.strategy = strategy_class(kwargs.get('tardanzas_semana', 0))
        else:
            self.strategy = strategy_class()
        
        logger.info(f"Calculador inicializado con estrategia: {self.strategy.get_descripcion()}")
    
    def calcular_descuento(
        self, 
        minutos_tardanza: int, 
        salario_hora: Decimal
    ) -> Dict[str, Any]:
        """
        Calcula el descuento usando la estrategia configurada
        
        Args:
            minutos_tardanza (int): Minutos de tardanza
            salario_hora (Decimal): Salario por hora del docente
            
        Returns:
            Dict: Información del descuento calculado
        """
        try:
            descuento = self.strategy.calcular_descuento(minutos_tardanza, salario_hora)
            
            return {
                'descuento': descuento,
                'minutos_tardanza': minutos_tardanza,
                'salario_hora': salario_hora,
                'estrategia': self.strategy.get_descripcion(),
                'porcentaje_descuento': float((descuento / salario_hora) * 100) if salario_hora > 0 else 0,
                'tiene_descuento': descuento > 0
            }
        except Exception as e:
            logger.error(f"Error calculando descuento: {str(e)}")
            return {
                'descuento': Decimal('0.00'),
                'minutos_tardanza': minutos_tardanza,
                'salario_hora': salario_hora,
                'estrategia': self.strategy.get_descripcion(),
                'porcentaje_descuento': 0,
                'tiene_descuento': False,
                'error': str(e)
            }
    
    def cambiar_estrategia(self, nueva_estrategia: str, **kwargs):
        """
        Cambia la estrategia de cálculo
        
        Args:
            nueva_estrategia (str): Nombre de la nueva estrategia
            **kwargs: Argumentos adicionales para la nueva estrategia
        """
        if nueva_estrategia not in self.ESTRATEGIAS:
            raise ValueError(f"Estrategia '{nueva_estrategia}' no válida")
        
        strategy_class = self.ESTRATEGIAS[nueva_estrategia]
        
        if nueva_estrategia == 'semanal':
            self.strategy = strategy_class(kwargs.get('tardanzas_semana', 0))
        else:
            self.strategy = strategy_class()
        
        logger.info(f"Estrategia cambiada a: {self.strategy.get_descripcion()}")
    
    @classmethod
    def obtener_estrategias_disponibles(cls) -> Dict[str, str]:
        """
        Retorna las estrategias disponibles con sus descripciones
        
        Returns:
            Dict: Estrategias disponibles
        """
        estrategias = {}
        for nombre, strategy_class in cls.ESTRATEGIAS.items():
            if nombre == 'semanal':
                strategy = strategy_class()
            else:
                strategy = strategy_class()
            estrategias[nombre] = strategy.get_descripcion()
        
        return estrategias
