"""
Inicialización del microservicio de reportes

Importa Celery para asegurar que esté disponible al iniciar Django.
"""

from __future__ import absolute_import, unicode_literals

# Esto asegura que la aplicación siempre sea importada cuando Django se inicie
from .celery import app as celery_app

__all__ = ('celery_app',)