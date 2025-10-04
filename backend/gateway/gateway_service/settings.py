import pymysql
pymysql.install_as_MySQLdb()

"""
Django settings for gateway_service project.
API Gateway - Sistema Pontificia
Puerto: 8000
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-gateway-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_ratelimit',
    
    # Local apps
    'gateway_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 'gateway_app.middleware.RateLimitMiddleware',  # Desactivado temporalmente para tests
    # 'gateway_app.middleware.JWTValidationMiddleware',  # Desactivado temporalmente para tests
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gateway_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'gateway_service.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'gateway_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'root'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3313'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# API GATEWAY CONFIGURATION
# =============================================================================

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Spectacular (OpenAPI/Swagger) Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'Sistema Pontificia API Gateway',
    'DESCRIPTION': 'API Gateway centralizada para todos los microservicios del Sistema Pontificia',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Auth', 'description': 'Autenticación y autorización'},
        {'name': 'Users', 'description': 'Gestión de usuarios'},
        {'name': 'Attendance', 'description': 'Control de asistencias'},
        {'name': 'Payments', 'description': 'Gestión de pagos'},
        {'name': 'Documents', 'description': 'Gestión de documentos'},
        {'name': 'Reports', 'description': 'Generación de reportes'},
        {'name': 'Audit', 'description': 'Auditoría del sistema'},
        {'name': 'Gateway', 'description': 'Funciones del API Gateway'},
    ],
    'CONTACT': {
        'name': 'Sistema Pontificia',
        'email': 'desarrollo@pontificia.edu',
    },
    'LICENSE': {
        'name': 'Proyecto Académico',
    },
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True').lower() == 'true'

# =============================================================================
# MICROSERVICES CONFIGURATION
# =============================================================================

MICROSERVICES = {
    'auth': {
        'url': os.environ.get('AUTH_SERVICE_URL', 'http://localhost:3001'),
        'timeout': 30,
        'retry_attempts': 3,
        'health_endpoint': '/api/health/',
    },
    'users': {
        'url': os.environ.get('USERS_SERVICE_URL', 'http://localhost:3002'),
        'timeout': 30,
        'retry_attempts': 3,
        'health_endpoint': '/api/health/',
    },
    'attendance': {
        'url': os.environ.get('ATTENDANCE_SERVICE_URL', 'http://localhost:3003'),
        'timeout': 30,
        'retry_attempts': 3,
        'health_endpoint': '/api/health/',
    },
    'payments': {
        'url': os.environ.get('PAYMENTS_SERVICE_URL', 'http://localhost:3004'),
        'timeout': 30,
        'retry_attempts': 3,
        'health_endpoint': '/api/health/',
    },
    'documents': {
        'url': os.environ.get('DOCUMENTS_SERVICE_URL', 'http://localhost:3005'),
        'timeout': 30,
        'retry_attempts': 3,
        'health_endpoint': '/api/health/',
    },
    'reports': {
        'url': os.environ.get('REPORTS_SERVICE_URL', 'http://localhost:3006'),
        'timeout': 30,
        'retry_attempts': 3,
        'health_endpoint': '/api/health/',
    },
    'audit': {
        'url': os.environ.get('AUDIT_SERVICE_URL', 'http://localhost:3007'),
        'timeout': 30,
        'retry_attempts': 3,
        'health_endpoint': '/api/health/',
    },
}

# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================

# Rate limiting settings
RATELIMIT_ENABLE = os.environ.get('RATELIMIT_ENABLE', 'True').lower() == 'true'
RATELIMIT_USE_CACHE = 'default'

# Rate limits per endpoint type
RATE_LIMITS = {
    'default': '100/h',  # 100 requests per hour by default
    'auth': '20/m',      # Auth endpoints: 20 requests per minute
    'upload': '10/m',    # Upload endpoints: 10 requests per minute
    'download': '50/m',  # Download endpoints: 50 requests per minute
    'reports': '30/m',   # Reports: 30 requests per minute
}

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================

# Redis cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'gateway',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.environ.get('LOG_FILE', 'gateway.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'gateway': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# =============================================================================
# GATEWAY SPECIFIC SETTINGS
# =============================================================================

# Gateway configuration
GATEWAY_CONFIG = {
    'ENABLE_PROXY': os.environ.get('GATEWAY_ENABLE_PROXY', 'True').lower() == 'true',
    'ENABLE_JWT_VALIDATION': os.environ.get('GATEWAY_ENABLE_JWT_VALIDATION', 'True').lower() == 'true',
    'ENABLE_RATE_LIMITING': os.environ.get('GATEWAY_ENABLE_RATE_LIMITING', 'True').lower() == 'true',
    'ENABLE_HEALTH_CHECKS': os.environ.get('GATEWAY_ENABLE_HEALTH_CHECKS', 'True').lower() == 'true',
    'PROXY_TIMEOUT': int(os.environ.get('GATEWAY_PROXY_TIMEOUT', '30')),
    'HEALTH_CHECK_INTERVAL': int(os.environ.get('GATEWAY_HEALTH_CHECK_INTERVAL', '60')),
    'MAX_RETRY_ATTEMPTS': int(os.environ.get('GATEWAY_MAX_RETRY_ATTEMPTS', '3')),
}

# Circuit breaker settings
CIRCUIT_BREAKER = {
    'failure_threshold': 5,
    'recovery_timeout': 60,
    'expected_exception': Exception,
}

# Rate limiting settings
RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.environ.get('RATE_LIMIT_REQUESTS_PER_MINUTE', '60'))
RATE_LIMIT_REQUESTS_PER_HOUR = int(os.environ.get('RATE_LIMIT_REQUESTS_PER_HOUR', '1000'))

# JWT validation settings
JWT_VALIDATION_ENABLED = os.environ.get('JWT_VALIDATION_ENABLED', 'False').lower() == 'true'

