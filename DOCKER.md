# Documentación Docker - Sistema Pontificia

## 🐳 Resumen Ejecutivo

Esta documentación detalla la arquitectura de containerización del Sistema Pontificia, incluyendo configuraciones de Docker, Docker Compose, networking, volúmenes, y best practices para despliegue y mantenimiento.

## 🏗️ Arquitectura de Contenedores

### Vista General del Sistema

```
Sistema Pontificia - Docker Architecture
├── 🚪 Gateway (Port 8000)          # Nginx + Django
├── 🔐 Auth Service (Port 3001)     # Django + MySQL
├── 👥 Users Service (Port 3002)    # Django + MySQL  
├── 📝 Asistencia (Port 3003)       # Django + MySQL
├── 📄 Documentos (Port 3004)       # Django + MySQL
├── 💰 Pagos (Port 3005)           # Django + MySQL
├── 📊 Reportes (Port 3006)         # Django + MySQL
├── 🔍 Auditoria (Port 3007)        # Django + MySQL
├── 🗄️ Redis Cache (Port 6379)      # Redis 7-alpine
└── 🐬 MySQL Cluster               # 8 MySQL 8.0 instances
    ├── auth_mysql (Port 3307)
    ├── users_mysql (Port 3308)
    ├── asistencia_mysql (Port 3309)
    ├── documentos_mysql (Port 3310)
    ├── pagos_mysql (Port 3311)
    ├── reportes_mysql (Port 3312)
    ├── auditoria_mysql (Port 3313)
    └── gateway_mysql (Port 3314)
```

### Networking Architecture

```
Docker Network: pontificia_network (bridge)
┌─────────────────────────────────────────────────┐
│                  pontificia_network             │
│                                                 │
│  ┌─────────────┐    ┌─────────────┐             │
│  │   Gateway   │    │    Redis    │             │
│  │  (port 8000)│◄──►│ (port 6379) │             │
│  └─────────────┘    └─────────────┘             │
│         │                                       │
│         ▼                                       │
│  ┌─────────────────────────────────────────────┐│
│  │           Microservices Layer              ││
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  ││
│  │  │Auth │ │Users│ │Asis │ │Docs │ │Pagos│  ││
│  │  │3001 │ │3002 │ │3003 │ │3004 │ │3005 │  ││
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘  ││
│  │  ┌─────┐ ┌─────┐                          ││
│  │  │Repor│ │Audit│                          ││
│  │  │3006 │ │3007 │                          ││
│  │  └─────┘ └─────┘                          ││
│  └─────────────────────────────────────────────┘│
│         │                                       │
│         ▼                                       │
│  ┌─────────────────────────────────────────────┐│
│  │             Database Layer                 ││
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  ││
│  │  │3307 │ │3308 │ │3309 │ │3310 │ │3311 │  ││
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘  ││
│  │  ┌─────┐ ┌─────┐ ┌─────┐                  ││
│  │  │3312 │ │3313 │ │3314 │                  ││
│  │  └─────┘ └─────┘ └─────┘                  ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

## 📦 Configuración de Contenedores

### Docker-compose.yml Principal

```yaml
version: '3.8'

services:
  # Redis Cache Service
  redis:
    image: redis:7-alpine
    container_name: pontificia_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - pontificia_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MySQL Database Services (One per microservice)
  auth_mysql:
    image: mysql:8.0
    container_name: pontificia_auth_mysql
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: auth_db
      MYSQL_USER: auth_user
      MYSQL_PASSWORD: auth_password
    ports:
      - "3307:3306"
    volumes:
      - auth_mysql_data:/var/lib/mysql
      - ./mysql/init/auth:/docker-entrypoint-initdb.d
    networks:
      - pontificia_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-proot_password"]
      interval: 30s
      timeout: 10s
      retries: 5

  # [Similar configuration for all other MySQL instances...]

  # Microservices
  auth:
    build: 
      context: ./auth_service
      dockerfile: Dockerfile
    container_name: pontificia_auth
    ports:
      - "3001:8000"
    environment:
      - DEBUG=False
      - DB_HOST=auth_mysql
      - DB_NAME=auth_db
      - DB_USER=auth_user
      - DB_PASSWORD=auth_password
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      auth_mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - pontificia_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - auth_logs:/app/logs

  # [Similar configuration for all other microservices...]

networks:
  pontificia_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  redis_data:
  auth_mysql_data:
  users_mysql_data:
  asistencia_mysql_data:
  documentos_mysql_data:
  pagos_mysql_data:
  reportes_mysql_data:
  auditoria_mysql_data:
  gateway_mysql_data:
  auth_logs:
  users_logs:
  documentos_files:
  reportes_exports:
```

### Dockerfiles Individuales

#### Auth Service Dockerfile

```dockerfile
# auth_service/Dockerfile
FROM python:3.11-slim

# Metadata
LABEL maintainer="Sistema Pontificia Team"
LABEL version="1.0.0"
LABEL description="Auth microservice for Sistema Pontificia"

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose port
EXPOSE 8000

# Startup script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
```

#### Gateway Service Dockerfile

```dockerfile
# gateway_service/Dockerfile  
FROM python:3.11-slim

# Install system dependencies including nginx
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directories and set permissions
RUN mkdir -p /var/log/supervisor /var/log/nginx /app/logs
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app /var/log/supervisor

# Environment variables
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Use supervisor to manage nginx + django
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

### Entrypoint Scripts

#### auth_service/entrypoint.sh

```bash
#!/bin/bash
set -e

echo "🚀 Starting Auth Service..."

# Wait for database
echo "⏳ Waiting for database..."
while ! nc -z $DB_HOST 3306; do
  sleep 1
done
echo "✅ Database is ready!"

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@pontificia.com', 'admin_password')
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
EOF

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start application
echo "🎯 Starting Django server..."
exec "$@"
```

## 🔧 Configuración de Servicios

### Variables de Entorno

#### Archivo .env Principal

```env
# Production Environment Variables
COMPOSE_PROJECT_NAME=pontificia

# Database Configuration
MYSQL_ROOT_PASSWORD=root_password
MYSQL_VERSION=8.0

# Redis Configuration  
REDIS_VERSION=7-alpine

# Application Configuration
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,pontificia.local

# Security
SECURE_SSL_REDIRECT=False
SECURE_SSL_HOST=False
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_MAX_REQUESTS=1000
```

#### Variables por Microservicio

**Auth Service (.env.auth)**
```env
SERVICE_NAME=auth
DB_HOST=auth_mysql
DB_NAME=auth_db
DB_USER=auth_user
DB_PASSWORD=auth_password
DB_PORT=3306

REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=auth-jwt-secret-key
JWT_EXPIRATION_TIME=3600

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

**Users Service (.env.users)**
```env
SERVICE_NAME=users
DB_HOST=users_mysql
DB_NAME=users_db
DB_USER=users_user
DB_PASSWORD=users_password
DB_PORT=3306

REDIS_URL=redis://redis:6379/1
AUTH_SERVICE_URL=http://auth:8000

MEDIA_ROOT=/app/media
MEDIA_URL=/media/
FILE_UPLOAD_MAX_MEMORY_SIZE=5242880
```

### Configuración de Health Checks

#### Health Check Endpoints

Cada servicio implementa múltiples health checks:

```python
# health/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """General health check"""
    try:
        # Database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Cache check
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check')
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected' if cache_status == 'ok' else 'disconnected',
            'service': request.resolver_match.app_name
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)

def database_health(request):
    """Database-specific health check"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
        
        return JsonResponse({
            'status': 'healthy',
            'database': {
                'connected': True,
                'version': version
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': {
                'connected': False,
                'error': str(e)
            }
        }, status=503)
```

## 🚀 Comandos de Despliegue

### Despliegue Completo

```bash
# 1. Construir y levantar todos los servicios
docker-compose up --build -d

# 2. Verificar estado de contenedores
docker ps

# 3. Verificar health checks
docker-compose ps

# 4. Ver logs de inicialización
docker-compose logs --tail=50

# 5. Ejecutar migraciones en todos los servicios
./scripts/run_migrations.sh

# 6. Verificar conectividad entre servicios
./scripts/test_connectivity.sh
```

### Scripts de Automatización

#### run_migrations.sh

```bash
#!/bin/bash
echo "🔄 Running migrations on all microservices..."

services=("auth" "users" "asistencia" "documentos" "pagos" "reportes" "auditoria" "gateway")

for service in "${services[@]}"; do
    echo "📦 Running migrations for $service..."
    docker exec pontificia_$service python manage.py migrate --noinput
    if [ $? -eq 0 ]; then
        echo "✅ $service migrations completed"
    else
        echo "❌ $service migrations failed"
        exit 1
    fi
done

echo "🎉 All migrations completed successfully!"
```

#### test_connectivity.sh

```bash
#!/bin/bash
echo "🌐 Testing connectivity between services..."

# Test database connections
services=("auth" "users" "asistencia" "documentos" "pagos" "reportes" "auditoria" "gateway")

for service in "${services[@]}"; do
    echo "🔍 Testing $service database connection..."
    docker exec pontificia_$service python manage.py shell << EOF
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✅ $service database connection successful")
except Exception as e:
    print(f"❌ $service database connection failed: {e}")
EOF
done

# Test Redis connection
echo "🔍 Testing Redis connection..."
docker exec pontificia_redis redis-cli ping
if [ $? -eq 0 ]; then
    echo "✅ Redis connection successful"
else
    echo "❌ Redis connection failed"
fi

# Test inter-service HTTP connectivity
echo "🔍 Testing service-to-service HTTP connectivity..."
docker exec pontificia_gateway curl -f http://auth:8000/health/ --max-time 5
docker exec pontificia_gateway curl -f http://users:8000/health/ --max-time 5

echo "🎉 Connectivity tests completed!"
```

## 📊 Monitoreo y Logging

### Configuración de Logging

#### logstash.conf

```ruby
# logstash/logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [container][name] {
    mutate {
      add_field => { "service_name" => "%{[container][name]}" }
    }
  }
  
  if [message] =~ /^\{/ {
    json {
      source => "message"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "pontificia-logs-%{+YYYY.MM.dd}"
  }
}
```

### Métricas y Monitoreo

#### Prometheus Configuration

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'pontificia-services'
    static_configs:
      - targets: 
        - 'auth:8000'
        - 'users:8000'
        - 'asistencia:8000'
        - 'documentos:8000'
        - 'pagos:8000'
        - 'reportes:8000'
        - 'auditoria:8000'
        - 'gateway:8000'
    metrics_path: '/metrics/'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'mysql'
    static_configs:
      - targets: 
        - 'auth_mysql:3306'
        - 'users_mysql:3306'
        # ... otros mysql instances
```

### Dashboard de Monitoreo

#### Grafana Dashboard JSON

```json
{
  "dashboard": {
    "title": "Sistema Pontificia - Microservices",
    "panels": [
      {
        "title": "Service Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"pontificia-services\"}",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "mysql_global_status_threads_connected",
            "legendFormat": "{{instance}}"
          }
        ]
      }
    ]
  }
}
```

## 🔒 Configuración de Seguridad

### Network Security

```yaml
# docker-compose.security.yml
version: '3.8'

services:
  # All services with restricted networking
  auth:
    networks:
      pontificia_internal:
        aliases:
          - auth-service
    ports: [] # No external ports except through gateway

  gateway:
    networks:
      - pontificia_external
      - pontificia_internal
    ports:
      - "80:80"
      - "443:443"
    
networks:
  pontificia_external:
    driver: bridge
  pontificia_internal:
    driver: bridge
    internal: true # No external access
```

### SSL/TLS Configuration

#### nginx.conf for Gateway

```nginx
upstream django_app {
    server gateway:8000;
}

server {
    listen 80;
    server_name pontificia.local localhost;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name pontificia.local localhost;

    ssl_certificate /etc/ssl/certs/pontificia.crt;
    ssl_certificate_key /etc/ssl/private/pontificia.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔧 Mantenimiento y Troubleshooting

### Comandos de Diagnóstico

```bash
# Verificar estado de contenedores
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Verificar uso de recursos
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Verificar logs de un servicio específico
docker logs pontificia_auth --tail 100 --follow

# Verificar conectividad de red
docker network inspect pontificia_network

# Verificar volúmenes
docker volume ls | grep pontificia

# Test de conectividad entre servicios
docker exec pontificia_gateway nc -zv auth 8000
docker exec pontificia_gateway nc -zv redis 6379

# Backup de base de datos
docker exec pontificia_auth_mysql mysqldump -u root -proot_password auth_db > backup_auth.sql

# Restaurar base de datos
docker exec -i pontificia_auth_mysql mysql -u root -proot_password auth_db < backup_auth.sql
```

### Troubleshooting Común

#### 1. Contenedor no inicia

```bash
# Ver logs detallados
docker logs pontificia_gateway --details

# Verificar si el puerto está ocupado
netstat -tlnp | grep :8000

# Reiniciar contenedor específico
docker restart pontificia_gateway

# Reconstruir contenedor
docker-compose up --build --force-recreate gateway
```

#### 2. Base de datos no conecta

```bash
# Verificar estado de MySQL
docker exec pontificia_auth_mysql mysqladmin ping -u root -proot_password

# Verificar variables de entorno
docker exec pontificia_auth env | grep DB_

# Test de conexión manual
docker exec -it pontificia_auth python manage.py dbshell
```

#### 3. Problemas de networking

```bash
# Verificar red Docker
docker network ls
docker network inspect pontificia_network

# Test de DNS resolution
docker exec pontificia_gateway nslookup auth
docker exec pontificia_gateway nslookup redis

# Verificar routing
docker exec pontificia_gateway route -n
```

### Scripts de Backup

#### backup.sh

```bash
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "🗄️ Starting backup process..."

# Database backups
services=("auth" "users" "asistencia" "documentos" "pagos" "reportes" "auditoria" "gateway")

for service in "${services[@]}"; do
    echo "💾 Backing up ${service} database..."
    docker exec pontificia_${service}_mysql mysqldump \
        -u root -proot_password ${service}_db \
        > $BACKUP_DIR/${service}_db.sql
done

# Redis backup
echo "💾 Backing up Redis data..."
docker exec pontificia_redis redis-cli BGSAVE
docker cp pontificia_redis:/data/dump.rdb $BACKUP_DIR/redis_dump.rdb

# Application data
echo "💾 Backing up application volumes..."
docker run --rm -v pontificia_documentos_files:/data -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/documentos_files.tar.gz -C /data .

echo "✅ Backup completed in $BACKUP_DIR"
```

### Performance Optimization

#### Resource Limits

```yaml
# docker-compose.override.yml for production
version: '3.8'

services:
  auth:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    
  users:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

  gateway:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  auth_mysql:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

## 📋 Checklist de Despliegue

### Pre-despliegue
- [ ] Verificar disponibilidad de puertos (3001-3007, 8000, 3307-3313, 6379)
- [ ] Validar configuración de variables de entorno
- [ ] Verificar espacio en disco (mínimo 10GB)
- [ ] Confirmar versiones de Docker (20.0+) y Docker Compose (2.0+)
- [ ] Revisar configuración de firewall

### Durante el despliegue
- [ ] Ejecutar `docker-compose up --build -d`
- [ ] Verificar que todos los contenedores estén healthy
- [ ] Ejecutar migraciones de base de datos
- [ ] Verificar logs de inicialización
- [ ] Testear health checks de todos los servicios

### Post-despliegue
- [ ] Verificar conectividad entre servicios
- [ ] Ejecutar tests de integración
- [ ] Configurar monitoring y alertas
- [ ] Verificar backups automáticos
- [ ] Documentar configuración específica del entorno

## 📞 Soporte

Para issues relacionados con Docker:
- **Logs**: `docker-compose logs <service>`
- **Estado**: `docker ps -a`
- **Networking**: `docker network inspect pontificia_network`
- **Volumes**: `docker volume ls`
- **Performance**: `docker stats`

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2024  
**Mantenido por**: DevOps Team - Sistema Pontificia