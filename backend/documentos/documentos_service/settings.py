import pymysql
pymysql.install_as_MySQLdb()

"""
Django settings for documentos_service project.

Configuración específica para el microservicio DOCUMENTOS
Puerto: 3004
Base de Datos: documentos_db (MySQL puerto 3310)
"""

import os
from pathlib import Path
try:
    from decouple import config, Csv
except ImportError:
    # Fallback si decouple no está disponible
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            return cast(value)
        return value
    
    def Csv():
        return lambda x: x.split(',') if x else []

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CORE SETTINGS
# ==============================================================================

SECRET_KEY = config(
    'SECRET_KEY',
    default='documentos-secret-key-change-in-production-2024'
)

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
]

LOCAL_APPS = [
    'documentos_app',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================================================================
# URLS AND WSGI
# ==============================================================================

ROOT_URLCONF = 'documentos_service.urls'
WSGI_APPLICATION = 'documentos_service.wsgi.application'

# ==============================================================================
# TEMPLATES
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==============================================================================
# DATABASE
# ==============================================================================

# Database configuration using environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'documentos_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'root'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3310'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'sql_mode': 'STRICT_TRANS_TABLES',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# ==============================================================================
# MEDIA FILES (Uploads)
# ==============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# REST FRAMEWORK
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# ==============================================================================
# JWT SETTINGS
# ==============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# ==============================================================================
# CORS SETTINGS
# ==============================================================================

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173',
    cast=Csv()
)

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Solo en desarrollo

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-forwarded-for',
    'x-forwarded-proto',
]

# ==============================================================================
# SERVICIOS EXTERNOS
# ==============================================================================

# URLs de otros microservicios
AUTH_SERVICE_URL = config('AUTH_SERVICE_URL', default='http://localhost:8001')
USERS_SERVICE_URL = config('USERS_SERVICE_URL', default='http://localhost:8002')
ASISTENCIA_SERVICE_URL = config('ASISTENCIA_SERVICE_URL', default='http://localhost:3003')

# Timeouts para servicios externos
AUTH_SERVICE_TIMEOUT = config('AUTH_SERVICE_TIMEOUT', default=30, cast=int)
USERS_SERVICE_TIMEOUT = config('USERS_SERVICE_TIMEOUT', default=30, cast=int)

# ==============================================================================
# SEGURIDAD
# ==============================================================================

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Security settings
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookie settings
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

# ==============================================================================
# DEFAULT SETTINGS
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# CONFIGURACIÓN ESPECÍFICA DEL SERVICIO DE DOCUMENTOS
# ==============================================================================

# Configuración de archivos
MAX_FILE_SIZE = config('MAX_FILE_SIZE', default=50*1024*1024, cast=int)  # 50MB
ALLOWED_FILE_TYPES = config(
    'ALLOWED_FILE_TYPES', 
    default='pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,jpeg,png,gif',
    cast=Csv()
)

# Configuración de versionado
MAX_VERSIONS_PER_DOCUMENT = config('MAX_VERSIONS_PER_DOCUMENT', default=10, cast=int)

# Configuración de flujo de documentos
FLUJO_ESTADOS = [
    'CREADO',
    'EN_REVISION',
    'APROBADO',
    'RECHAZADO',
    'FIRMADO',
    'PUBLICADO',
    'ARCHIVADO'
]

# Configuración de notificaciones
NOTIFICACIONES_ENABLED = config('NOTIFICACIONES_ENABLED', default=True, cast=bool)

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'static', exist_ok=True)
os.makedirs(BASE_DIR / 'media', exist_ok=True)

