from django.apps import AppConfig


class PagosAppConfig(AppConfig):
    """
    Configuración de la aplicación de pagos
    
    Define la configuración principal de la app incluyendo
    señales y configuraciones específicas.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pagos_app'
    verbose_name = 'Sistema de Pagos'
    
    def ready(self):
        """
        Ejecuta código cuando la aplicación está lista
        
        Importa las señales para que se registren correctamente.
        """
        try:
            # Importar señales si las hay
            # import pagos_app.signals
            pass
        except ImportError:
            pass
