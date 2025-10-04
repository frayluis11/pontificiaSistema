# Sistema Pontificia - API Gateway

## Descripción

El API Gateway es el punto de entrada centralizado para todos los microservicios del Sistema Pontificia. Proporciona un único endpoint que actúa como proxy hacia los diferentes servicios, implementando funcionalidades transversales como autenticación JWT, rate limiting, y monitoreo de salud.

## Características Principales

- **Proxy Inteligente**: Enruta peticiones a los microservicios correspondientes
- **Documentación OpenAPI**: Interfaz Swagger automática en `/api/docs/`
- **Health Check**: Monitoreo del estado de todos los microservicios
- **Rate Limiting**: Limitación de peticiones por IP (configurable)
- **Autenticación JWT**: Validación de tokens en endpoints protegidos
- **CORS**: Configuración para peticiones cross-origin
- **Cache**: Sistema de cache configurable con Redis/locmem

## Arquitectura

### Puerto y Configuración
- **Puerto**: 8000
- **Framework**: Django 4.2.7 + Django REST Framework 3.14.0
- **Documentación**: drf-spectacular 0.26.5
- **Base de datos**: SQLite (para desarrollo)
- **Cache**: Redis con fallback a locmem

### Microservicios Integrados

| Servicio | Puerto | Endpoint Base | Descripción |
|----------|--------|---------------|-------------|
| Auth | 3001 | `/api/auth/` | Autenticación y autorización |
| Users | 3002 | `/api/users/` | Gestión de usuarios |
| Asistencia | 3003 | `/api/asistencia/` | Control de asistencia |
| Documentos | 3004 | `/api/documentos/` | Gestión documental |
| Pagos | 3005 | `/api/pagos/` | Sistema de pagos |
| Reportes | 3006 | `/api/reportes/` | Generación de reportes |
| Auditoría | 3007 | `/api/auditoria/` | Logs y auditoría |

## Instalación y Configuración

### Prerrequisitos

- Python 3.11+
- pip
- Git
- Redis (opcional, recomendado para producción)

### Instalación Paso a Paso

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd sistemaPontificia/backend/gateway
   ```

2. **Crear y activar entorno virtual**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   
   Crear archivo `.env` en la raíz del proyecto:
   ```env
   # Django Configuration
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Database
   DATABASE_URL=sqlite:///db.sqlite3
   
   # Cache Configuration
   REDIS_URL=redis://localhost:6379/1
   
   # Rate Limiting
   RATE_LIMIT_ENABLED=True
   RATE_LIMIT_REQUESTS_PER_MINUTE=60
   RATE_LIMIT_REQUESTS_PER_HOUR=1000
   
   # JWT Validation
   JWT_VALIDATION_ENABLED=True
   
   # Microservices URLs
   AUTH_SERVICE_URL=http://localhost:3001
   USERS_SERVICE_URL=http://localhost:3002
   ASISTENCIA_SERVICE_URL=http://localhost:3003
   DOCUMENTOS_SERVICE_URL=http://localhost:3004
   PAGOS_SERVICE_URL=http://localhost:3005
   REPORTES_SERVICE_URL=http://localhost:3006
   AUDITORIA_SERVICE_URL=http://localhost:3007
   ```

5. **Aplicar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario (opcional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Iniciar el servidor**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

## Uso del API Gateway

### Endpoints Principales

#### 1. Health Check
```
GET /health/
```
Retorna el estado de salud del gateway y todos los microservicios.

**Respuesta de ejemplo:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "gateway": {
    "status": "running",
    "version": "1.0.0",
    "port": 8000
  },
  "services": {
    "auth": {
      "status": "healthy",
      "url": "http://localhost:3001/api/health/"
    },
    "users": {
      "status": "healthy", 
      "url": "http://localhost:3002/api/health/"
    }
  },
  "summary": {
    "total_services": 7,
    "healthy_services": 6,
    "unhealthy_services": 1,
    "overall_health_percentage": 85.7
  }
}
```

#### 2. Documentación API
```
GET /api/docs/
```
Interfaz Swagger interactiva con la documentación completa de la API.

#### 3. Esquema OpenAPI
```
GET /api/schema/
```
Esquema OpenAPI 3.0 en formato JSON.

#### 4. Proxy a Microservicios

Todas las peticiones que siguen el patrón `/api/{servicio}/` son automáticamente enrutadas al microservicio correspondiente:

```bash
# Autenticación
POST /api/auth/login/
GET /api/auth/profile/

# Usuarios
GET /api/users/
POST /api/users/

# Asistencia
GET /api/asistencia/
POST /api/asistencia/registro/

# Documentos
GET /api/documentos/
POST /api/documentos/upload/

# Pagos
GET /api/pagos/
POST /api/pagos/proceso/

# Reportes
GET /api/reportes/
POST /api/reportes/generar/

# Auditoría
GET /api/auditoria/logs/
```

### Autenticación

El gateway soporta autenticación JWT. Para endpoints protegidos, incluir el header:

```
Authorization: Bearer <jwt-token>
```

**Endpoints excluidos de autenticación:**
- `/health/`
- `/api/docs/`
- `/api/schema/`
- `/admin/`
- `/api/auth/login/`
- `/api/auth/register/`

### Rate Limiting

El sistema implementa limitación de peticiones por IP:
- **Por defecto**: 60 peticiones/minuto, 1000 peticiones/hora
- **Configurable** mediante variables de entorno
- **Respuesta cuando se excede el límite**:
  ```json
  {
    "error": "Too many requests",
    "message": "Rate limit exceeded. Max 60 requests per minute.",
    "retry_after": 60
  }
  ```

## Desarrollo

### Estructura del Proyecto

```
gateway/
├── gateway_service/          # Configuración principal de Django
│   ├── settings.py          # Configuración del proyecto
│   ├── urls.py             # URLs principales
│   └── wsgi.py             # WSGI configuration
├── gateway_app/            # Aplicación principal del gateway
│   ├── simple_views.py     # Vistas y lógica de proxy
│   ├── simple_urls.py      # URLs de la aplicación
│   ├── middleware.py       # Middlewares personalizados
│   ├── tests.py           # Tests de integración
│   └── apps.py            # Configuración de la app
├── requirements.txt        # Dependencias de Python
├── manage.py              # Script de gestión de Django
└── README_Backend.md      # Esta documentación
```

### Middlewares Personalizados

#### 1. RateLimitMiddleware
- **Propósito**: Limitar peticiones por IP
- **Configuración**: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS_PER_MINUTE`, `RATE_LIMIT_REQUESTS_PER_HOUR`
- **Storage**: Cache de Django (Redis/locmem)

#### 2. JWTValidationMiddleware
- **Propósito**: Validar tokens JWT en endpoints protegidos
- **Configuración**: `JWT_VALIDATION_ENABLED`
- **Exclusiones**: Rutas configuradas en `excluded_paths`

### Tests

Ejecutar los tests de integración:

```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test gateway_app.tests.GatewayIntegrationTests

# Test específico
python manage.py test gateway_app.tests.GatewayIntegrationTests.test_health_check_endpoint

# Con mayor verbosidad
python manage.py test --verbosity=2
```

### Configuración de Cache

#### Para Desarrollo (locmem)
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'gateway-cache',
        'TIMEOUT': 300,
    }
}
```

#### Para Producción (Redis)
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Despliegue

### Desarrollo
```bash
python manage.py runserver 0.0.0.0:8000
```

### Producción con Gunicorn
```bash
# Instalar Gunicorn
pip install gunicorn

# Ejecutar
gunicorn gateway_service.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Docker (Opcional)

Crear `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "gateway_service.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Variables de Entorno para Producción

```env
DEBUG=False
SECRET_KEY=<secure-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost/gateway_db
REDIS_URL=redis://localhost:6379/1
RATE_LIMIT_ENABLED=True
JWT_VALIDATION_ENABLED=True
```

## Configuración de Nginx

Ejemplo de configuración para Nginx como reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/static/files/;
    }

    location /media/ {
        alias /path/to/media/files/;
    }
}
```

## Monitoreo y Logs

### Health Check Avanzado
El endpoint `/health/` proporciona información detallada:
- Estado del gateway
- Estado de cada microservicio
- Tiempo de respuesta
- Errores de conexión
- Estadísticas generales

### Logs
Los logs de Django se pueden configurar en `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'gateway.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'gateway_app': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Troubleshooting

### Problemas Comunes

1. **Error de conexión a microservicios**
   - Verificar que los microservicios estén ejecutándose
   - Revisar las URLs en la configuración
   - Comprobar conectividad de red

2. **Rate limiting no funciona**
   - Verificar configuración de cache
   - Revisar que `RATE_LIMIT_ENABLED=True`
   - Comprobar conexión a Redis

3. **JWT validation falla**
   - Verificar configuración de `rest_framework_simplejwt`
   - Revisar el formato del token en el header
   - Comprobar que `JWT_VALIDATION_ENABLED=True`

4. **Documentación no se muestra**
   - Verificar que `drf_spectacular` esté instalado
   - Revisar configuración en `settings.py`
   - Comprobar que `DEBUG=True` para desarrollo

### Comandos Útiles

```bash
# Verificar estado del servidor
curl http://localhost:8000/health/

# Probar endpoint de documentación
curl http://localhost:8000/api/docs/

# Verificar proxy (requiere microservicio ejecutándose)
curl http://localhost:8000/api/auth/status/

# Probar rate limiting
for i in {1..70}; do curl http://localhost:8000/health/; done
```

## Contacto y Soporte

Para soporte técnico o preguntas sobre el API Gateway:
- Revisar la documentación en `/api/docs/`
- Consultar los logs del sistema
- Ejecutar tests de integración para diagnosticar problemas

---

**Versión**: 1.0.0  
**Última actualización**: Octubre 2024  
**Autor**: Sistema Pontificia Team