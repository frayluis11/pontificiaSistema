"""
Excepciones personalizadas para el microservicio de reportes
"""


class ReporteServiceException(Exception):
    """
    Excepción base para errores del servicio de reportes
    """
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ReporteNoEncontradoException(ReporteServiceException):
    """Excepción cuando no se encuentra un reporte"""
    
    def __init__(self, reporte_id: str):
        message = f"Reporte con ID {reporte_id} no encontrado"
        super().__init__(message, "REPORTE_NO_ENCONTRADO")


class FormatoNoSoportadoException(ReporteServiceException):
    """Excepción para formatos no soportados"""
    
    def __init__(self, formato: str):
        message = f"Formato {formato} no soportado"
        super().__init__(message, "FORMATO_NO_SOPORTADO")


class ParametrosInvalidosException(ReporteServiceException):
    """Excepción para parámetros inválidos"""
    
    def __init__(self, parametro: str, detalle: str = None):
        message = f"Parámetro inválido: {parametro}"
        if detalle:
            message += f" - {detalle}"
        super().__init__(message, "PARAMETROS_INVALIDOS")


class ErrorProcesamiento(ReporteServiceException):
    """Excepción para errores durante el procesamiento"""
    
    def __init__(self, detalle: str):
        message = f"Error en procesamiento: {detalle}"
        super().__init__(message, "ERROR_PROCESAMIENTO")


class MetricaNoEncontradaException(ReporteServiceException):
    """Excepción cuando no se encuentra una métrica"""
    
    def __init__(self, nombre: str):
        message = f"Métrica '{nombre}' no encontrada"
        super().__init__(message, "METRICA_NO_ENCONTRADA")


class ArchivoNoEncontradoException(ReporteServiceException):
    """Excepción cuando no se encuentra un archivo"""
    
    def __init__(self, archivo: str):
        message = f"Archivo '{archivo}' no encontrado"
        super().__init__(message, "ARCHIVO_NO_ENCONTRADO")


class PermisosDenegadosException(ReporteServiceException):
    """Excepción para errores de permisos"""
    
    def __init__(self, accion: str):
        message = f"Permisos insuficientes para: {accion}"
        super().__init__(message, "PERMISOS_DENEGADOS")


class ReporteExpiradoException(ReporteServiceException):
    """Excepción cuando un reporte está expirado"""
    
    def __init__(self, reporte_id: str):
        message = f"El reporte {reporte_id} ha expirado"
        super().__init__(message, "REPORTE_EXPIRADO")


class CeleryNoDisponibleException(ReporteServiceException):
    """Excepción cuando Celery no está disponible"""
    
    def __init__(self):
        message = "Servicio de tareas asíncronas no disponible"
        super().__init__(message, "CELERY_NO_DISPONIBLE")