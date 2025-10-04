# Sistema Pontificia - Microservicios Backend

## 📋 Descripción General

Sistema Pontificia es una plataforma de gestión educativa basada en microservicios desarrollada con Django/Django REST Framework. El sistema maneja autenticación, gestión de usuarios, asistencia, documentos, pagos, reportes y auditoría de manera distribuida y escalable.

## 🏗️ Arquitectura de Microservicios

El sistema está compuesto por 8 microservicios principales:

### 🔐 Servicio de Autenticación (Puerto 3001)
- **Función**: Manejo de autenticación, autorización y tokens JWT
- **Endpoints principales**: `/auth/login/`, `/auth/register/`, `/auth/refresh/`
- **Base de datos**: MySQL independiente
- **Características**: JWT tokens, middleware de autenticación, validación de usuarios

### 👥 Servicio de Usuarios (Puerto 3002)
- **Función**: Gestión completa de usuarios del sistema
- **Endpoints principales**: `/users/`, `/users/profile/`, `/users/roles/`
- **Base de datos**: MySQL independiente
- **Características**: CRUD de usuarios, perfiles, roles y permisos

### 📝 Servicio de Asistencia (Puerto 3003)
- **Función**: Control y seguimiento de asistencia de estudiantes
- **Endpoints principales**: `/asistencia/registro/`, `/asistencia/reporte/`
- **Base de datos**: MySQL independiente
- **Características**: Registro de asistencia, reportes, estadísticas

### 📄 Servicio de Documentos (Puerto 3004)
- **Función**: Gestión y almacenamiento de documentos académicos
- **Endpoints principales**: `/documentos/upload/`, `/documentos/download/`
- **Base de datos**: MySQL independiente
- **Características**: Upload/download de archivos, metadata, versionado

### 💰 Servicio de Pagos (Puerto 3005)
- **Función**: Procesamiento y seguimiento de pagos académicos
- **Endpoints principales**: `/pagos/procesar/`, `/pagos/historial/`
- **Base de datos**: MySQL independiente
- **Características**: Integración con pasarelas de pago, historial, facturas

### 📊 Servicio de Reportes (Puerto 3006)
- **Función**: Generación de reportes y analytics del sistema
- **Endpoints principales**: `/reportes/generar/`, `/reportes/descargar/`
- **Base de datos**: MySQL independiente
- **Características**: Reportes PDF/Excel, gráficos, dashboards

### 🔍 Servicio de Auditoría (Puerto 3007)
- **Función**: Logging y auditoría de acciones del sistema
- **Endpoints principales**: `/auditoria/logs/`, `/auditoria/eventos/`
- **Base de datos**: MySQL independiente
- **Características**: Activity logging, trazabilidad, compliance

### 🚪 Gateway API (Puerto 8000)
- **Función**: Punto de entrada único, enrutamiento y rate limiting
- **Endpoints principales**: Proxy a todos los microservicios
- **Características**: Rate limiting, CORS, load balancing, health checks

## 🛠️ Tecnologías Utilizadas

- **Backend Framework**: Django 4.2+ con Django REST Framework
- **Base de Datos**: MySQL 8.0 (instancia independiente por microservicio)
- **Cache**: Redis 7-alpine
- **Containerización**: Docker & Docker Compose
- **Autenticación**: JWT (JSON Web Tokens)
- **API Documentation**: Django REST Framework Swagger
- **Testing**: Django TestCase, pytest
- **Networking**: Docker networks con health checks

## 📁 Estructura del Proyecto

```
sistemaPontificia/
├── auth_service/              # Servicio de Autenticación
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── users_service/             # Servicio de Usuarios
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── asistencia_service/        # Servicio de Asistencia
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── documentos_service/        # Servicio de Documentos
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── pagos_service/             # Servicio de Pagos
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── reportes_service/          # Servicio de Reportes
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── auditoria_service/         # Servicio de Auditoría
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── gateway_service/           # Gateway API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── ...
├── docker-compose.yml         # Orquestación de contenedores
├── README.md                  # Este archivo
├── TESTS.md                  # Documentación de testing
├── DOCKER.md                 # Documentación de Docker
└── API_DOCS.md               # Documentación de APIs
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Docker 20.0+
- Docker Compose 2.0+
- Git
- 8GB RAM mínimo (recomendado 16GB)
- Puertos disponibles: 3001-3007, 8000, 3307-3313, 6379

### Instalación Rápida

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd sistemaPontificia
```

2. **Construir y levantar todos los servicios**
```bash
docker-compose up --build -d
```

3. **Verificar que todos los servicios están corriendo**
```bash
docker ps
```

4. **Ejecutar migraciones (si es necesario)**
```bash
# Para cada servicio
docker exec pontificia_auth python manage.py migrate
docker exec pontificia_users python manage.py migrate
# ... repetir para cada servicio
```

5. **Acceder a los servicios**
- Gateway: http://localhost:8000
- Auth Service: http://localhost:3001
- Users Service: http://localhost:3002
- (etc...)

## 🔧 Configuración de Desarrollo

### Variables de Entorno

Cada microservicio utiliza las siguientes variables de entorno (configuradas automáticamente en Docker):

```env
DEBUG=False
SECRET_KEY=<auto-generado>
ALLOWED_HOSTS=*
DB_NAME=<servicio>_db
DB_USER=root
DB_PASSWORD=root_password
DB_HOST=<servicio>_mysql
DB_PORT=3306
REDIS_URL=redis://redis:6379/0
```

### Configuración de Base de Datos

Cada microservicio tiene su propia instancia de MySQL:
- `auth_mysql` - Puerto 3307
- `users_mysql` - Puerto 3308
- `asistencia_mysql` - Puerto 3309
- `documentos_mysql` - Puerto 3310
- `pagos_mysql` - Puerto 3311
- `reportes_mysql` - Puerto 3312
- `auditoria_mysql` - Puerto 3313

## 🧪 Testing

### Ejecutar Todas las Pruebas

```bash
# Dentro de contenedores
docker exec pontificia_auth python manage.py test
docker exec pontificia_users python manage.py test
# ... para cada servicio

# O usando el script automático
./run_all_tests.sh
```

### Resultados de Testing Recientes

- **Users Service**: 25 tests (23 ✅ passed, 1 ⚠️ error, 1 ❌ failure)
- **Gateway Service**: 30 tests (16 ✅ passed, 8 ❌ failures, 6 ⚠️ errors)
- **Auditoria Service**: 22 tests (3 ✅ passed, 6 ❌ failures, 12 ⚠️ errors)

Ver `TESTS.md` para detalles completos de testing.

## 🐳 Docker y Despliegue

### Comandos Docker Útiles

```bash
# Levantar servicios en background
docker-compose up -d

# Ver logs de un servicio específico
docker logs pontificia_gateway --tail 50

# Acceder a un contenedor
docker exec -it pontificia_auth bash

# Parar todos los servicios
docker-compose down

# Reconstruir servicios
docker-compose up --build --force-recreate
```

Ver `DOCKER.md` para documentación completa de containerización.

## 📖 Documentación API

Cada microservicio expone su documentación Swagger en:
- Auth: http://localhost:3001/swagger/
- Users: http://localhost:3002/swagger/
- Gateway: http://localhost:8000/swagger/

Ver `API_DOCS.md` para documentación completa de endpoints.

## 🔍 Monitoreo y Health Checks

### Health Check Endpoints

Cada servicio tiene un endpoint de health check:
- `GET /health/` - Estado general del servicio
- `GET /health/db/` - Estado de la base de datos
- `GET /health/cache/` - Estado del cache Redis

### Logs y Debugging

```bash
# Ver logs en tiempo real
docker-compose logs -f gateway

# Ver logs específicos por servicio
docker logs pontificia_users --since 1h

# Monitorear recursos
docker stats
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **Puerto ocupado**: Verificar que los puertos 3001-3007, 8000 estén libres
2. **Base de datos no conecta**: Esperar a que los contenedores MySQL estén completamente iniciados
3. **Memoria insuficiente**: Asegurar al menos 8GB RAM disponible
4. **Permisos de archivos**: En Linux/Mac verificar permisos de Docker socket

### Comandos de Diagnóstico

```bash
# Verificar estado de contenedores
docker ps -a

# Verificar redes
docker network ls

# Verificar volúmenes
docker volume ls

# Logs detallados
docker-compose logs --tail=100
```

## 👥 Contribución

1. Fork el proyecto
2. Crear branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo `LICENSE.md` para detalles.

## 📞 Soporte

Para soporte técnico:
- Documentación: Ver archivos `.md` en el repositorio
- Issues: Crear un issue en GitHub
- Wiki: Consultar la wiki del proyecto

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2024  
**Mantenido por**: Equipo de Desarrollo Sistema Pontificia

### Bases de Datos MySQL
- **mysql_auth** (Puerto 3307): Base de datos para autenticación
- **mysql_users** (Puerto 3308): Base de datos para gestión de usuarios
- **mysql_asistencia** (Puerto 3309): Base de datos para sistema de asistencia
- **mysql_documentos** (Puerto 3310): Base de datos para gestión de documentos
- **mysql_pagos** (Puerto 3311): Base de datos para sistema de pagos
- **mysql_reportes** (Puerto 3312): Base de datos para reportes y analytics
- **mysql_auditoria** (Puerto 3313): Base de datos para auditoría y logs

### Servicios de Infraestructura
- **redis** (Puerto 6379): Cache y broker para Celery
- **phpmyadmin** (Puerto 8080): Interfaz web para administrar las bases de datos
- **gateway** (Puerto 8000): API Gateway para enrutamiento de microservicios

### Microservicios (Cuando se implementen)
- **auth-service** (Puerto 8001): Servicio de autenticación
- **users-service** (Puerto 8002): Servicio de gestión de usuarios
- **asistencia-service** (Puerto 8003): Servicio de asistencia
- **documentos-service** (Puerto 8004): Servicio de documentos
- **pagos-service** (Puerto 8005): Servicio de pagos
- **reportes-service** (Puerto 8006): Servicio de reportes
- **auditoria-service** (Puerto 8007): Servicio de auditoría

## Acceso a las Bases de Datos

### Credenciales
- Usuario: `root`
- Contraseña: `root`

### Conexión desde aplicación
Las variables de entorno están configuradas en el archivo `.env`:

- `MYSQL_AUTH_PORT=3307`
- `MYSQL_USERS_PORT=3308`
- `MYSQL_ASISTENCIA_PORT=3309`
- `MYSQL_DOCUMENTOS_PORT=3310`
- `MYSQL_PAGOS_PORT=3311`
- `MYSQL_REPORTES_PORT=3312`
- `MYSQL_AUDITORIA_PORT=3313`

### phpMyAdmin
Accede a http://localhost:8080 para administrar las bases de datos desde la interfaz web.

## Dependencias Principales

- **Django 4.2.7**: Framework web
- **Django REST Framework**: API REST
- **djangorestframework-simplejwt**: Autenticación JWT
- **mysqlclient**: Cliente MySQL para Python
- **celery**: Cola de tareas asíncronas
- **redis**: Cache y broker de mensajes
- **drf-spectacular**: Documentación automática de API

## Arquitectura de Microservicios

### Estructura de Carpetas por Microservicio
```
backend/
├── auth/               # Microservicio de autenticación
│   ├── Dockerfile      # Imagen Docker independiente
│   └── entrypoint.sh   # Script de inicialización
├── users/              # Microservicio de usuarios
├── asistencia/         # Microservicio de asistencia
├── documentos/         # Microservicio de documentos
├── pagos/              # Microservicio de pagos
├── reportes/           # Microservicio de reportes
├── auditoria/          # Microservicio de auditoría
├── gateway/            # API Gateway
└── seed_all.py         # Script global de poblado de DB
```

### Scripts de Inicialización Automática

Cada microservicio incluye un `entrypoint.sh` que automáticamente:
1. Espera a que la base de datos esté lista
2. Ejecuta migraciones de Django
3. Crea superusuario por defecto
4. Ejecuta seeds de datos iniciales
5. Recolecta archivos estáticos
6. Inicia el servidor Gunicorn

### Poblado Automático de Bases de Datos

El script `seed_all.py` pobla automáticamente todas las bases de datos con datos de prueba:

**Para Windows:**
```cmd
cd scripts
seed_databases.bat
```

**Para Linux/Mac:**
```bash
cd scripts
chmod +x seed_databases.sh
./seed_databases.sh
```

## Próximos Pasos

1. Crear los proyectos Django individuales en cada microservicio
2. Configurar las aplicaciones específicas por servicio
3. Implementar modelos de datos por microservicio
4. Configurar el API Gateway con enrutamiento
5. Implementar autenticación JWT entre servicios
6. Crear endpoints REST para cada microservicio
7. Implementar comunicación entre microservicios
8. Configurar Celery para tareas asíncronas