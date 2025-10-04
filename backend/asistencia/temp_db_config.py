# Configuración temporal para SQLite
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_temp.sqlite3',
    }
}

print("🔄 Usando SQLite temporal para pruebas")