"""
Configuración de la aplicación de documentos

Define la configuración y inicialización de la aplicación
"""
from django.apps import AppConfig


class DocumentosAppConfig(AppConfig):
    """
    Configuración de la aplicación de documentos
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documentos_app'
    verbose_name = 'Servicio de Documentos'
    
    def ready(self):
        """
        Configuración que se ejecuta cuando la aplicación está lista
        """
        # Importar signals si los hubiera
        # import documentos_app.signals
        
        # Configurar logging específico de la aplicación
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Servicio de Documentos iniciado correctamente")
