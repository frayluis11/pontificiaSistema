"""
Excepciones personalizadas para el microservicio de pagos
"""


class PagoServiceException(Exception):
    """
    Excepción base para errores del servicio de pagos
    """
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class PlanillaException(PagoServiceException):
    """
    Excepción específica para errores de planillas
    """
    pass


class BoletaException(PagoServiceException):
    """
    Excepción específica para errores de boletas
    """
    pass


class AdelantoException(PagoServiceException):
    """
    Excepción específica para errores de adelantos
    """
    pass


class CalculoException(PagoServiceException):
    """
    Excepción específica para errores de cálculo
    """
    pass


class ValidationException(PagoServiceException):
    """
    Excepción para errores de validación
    """
    pass