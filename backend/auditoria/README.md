# Microservicio de Auditoría - Sistema Pontificia

## Descripción

Microservicio especializado en el registro y análisis de actividades del sistema, proporcionando capacidades completas de auditoría, monitoreo y generación de reportes para todos los microservicios del Sistema Pontificia.

## Características Principales

### 🔍 **Auditoría Completa**
- Registro automático de todas las actividades del sistema
- Seguimiento de cambios en documentos y pagos
- Monitoreo de sesiones de usuario y accesos
- Detección de actividades sospechosas

### 📊 **Análisis y Reportes**
- Estadísticas en tiempo real
- Métricas de rendimiento del sistema
- Exportación a múltiples formatos (CSV, Excel, PDF)
- Dashboards de actividad

### 🔗 **Integración Transparente**
- Middleware automático para todos los requests
- Webhooks para notificaciones de otros microservicios
- Observer pattern para cambios en tiempo real
- API REST completa para consultas

### 🛡️ **Seguridad y Compliance**
- Detección automática de intentos de acceso no autorizado
- Registro de actividades críticas del sistema
- Cumplimiento de estándares de auditoría
- Retención configurable de logs

## Arquitectura

```
Microservicio Auditoría (Puerto 3007)
├── auditoria_app/
│   ├── models.py          # Modelo ActividadSistema
│   ├── services.py        # Lógica de negocio
│   ├── repositories.py    # Acceso a datos
│   ├── views.py          # API REST endpoints
│   ├── serializers.py    # Serialización API
│   ├── middleware/       # Middleware de auditoría
│   │   ├── auditoria.py  # Middleware principal
│   │   └── observer.py   # Observer y webhooks
│   └── management/       # Comandos personalizados
└── auditoria_service/    # Configuración Django
```

## Instalación y Configuración

### Prerrequisitos
- Python 3.11+
- MySQL 8.0+
- Docker (opcional)

### Configuración Base de Datos

1. **Crear base de datos MySQL:**
```sql
CREATE DATABASE auditoria_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'auditoria_user'@'localhost' IDENTIFIED BY 'auditoria_password';
GRANT ALL PRIVILEGES ON auditoria_db.* TO 'auditoria_user'@'localhost';
```

2. **Variables de entorno:**
```bash
DJANGO_DEBUG=False
MYSQL_HOST=localhost
MYSQL_PORT=3313
MYSQL_DATABASE=auditoria_db
MYSQL_USER=auditoria_user
MYSQL_PASSWORD=auditoria_password
```

### Instalación

1. **Instalar dependencias:**
```bash
cd backend/auditoria
pip install -r requirements.txt
```

2. **Ejecutar migraciones:**
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Crear superusuario (opcional):**
```bash
python manage.py createsuperuser
```

4. **Generar datos de prueba:**
```bash
python manage.py seed_auditoria --cantidad 500 --dias 30
```

5. **Ejecutar servidor:**
```bash
python manage.py runserver 0.0.0.0:3007
```

## API Endpoints

### 🔍 **Consulta de Logs**

#### `GET /api/logs/`
Lista todas las actividades con filtros y paginación.

**Parámetros:**
- `usuario_id`: Filtrar por usuario
- `accion`: Filtrar por tipo de acción
- `recurso`: Filtrar por recurso
- `microservicio`: Filtrar por microservicio
- `fecha_hora__gte`: Desde fecha
- `fecha_hora__lte`: Hasta fecha
- `exito`: Solo exitosas (true) o fallidas (false)
- `search`: Búsqueda en texto libre
- `ordering`: Ordenar por campo (-fecha_hora por defecto)

**Ejemplo:**
```bash
curl "http://localhost:3007/api/logs/?usuario_id=1&accion=LOGIN&ordering=-fecha_hora"
```

#### `GET /api/logs/{id}/`
Detalle de una actividad específica.

### 📊 **Estadísticas y Análisis**

#### `GET /api/logs/estadisticas/`
Estadísticas generales de auditoría.

**Parámetros:**
- `dias`: Período en días (default: 7)
- `usuario_id`: Estadísticas de usuario específico
- `microservicio`: Estadísticas de microservicio específico

**Respuesta:**
```json
{
  "total_actividades": 1500,
  "actividades_exitosas": 1350,
  "actividades_fallidas": 150,
  "tasa_exito": 90.0,
  "usuarios_unicos": 25,
  "duracion_promedio": 245.5,
  "por_accion": {
    "READ": 800,
    "CREATE": 300,
    "UPDATE": 250,
    "DELETE": 50
  },
  "por_microservicio": {
    "USERS": 400,
    "DOCUMENTS": 350,
    "PAYMENTS": 300
  }
}
```

#### `GET /api/logs/actividad_sospechosa/`
Detecta y retorna actividades sospechosas.

#### `GET /api/logs/metricas_rendimiento/` (Admin)
Métricas detalladas de rendimiento del sistema.

### 📄 **Exportación**

#### `GET /api/logs/exportar_csv/`
Exporta logs a formato CSV.

#### `GET /api/logs/exportar_excel/`
Exporta logs a formato Excel con formato.

#### `GET /api/logs/exportar_pdf/`
Exporta logs a formato PDF.

**Parámetros comunes de exportación:**
- `fecha_inicio`: Fecha inicio (ISO format)
- `fecha_fin`: Fecha fin (ISO format)
- `usuario_id`: Filtrar por usuario
- `accion`: Filtrar por acción
- `recurso`: Filtrar por recurso
- `microservicio`: Filtrar por microservicio

### 🔗 **Webhooks**

#### `POST /api/webhooks/documents/`
Recibe notificaciones de cambios en documentos.

**Payload:**
```json
{
  "action": "CREATE|UPDATE|DELETE",
  "document_id": "doc_123",
  "user_id": 1,
  "details": {
    "filename": "certificate.pdf",
    "size": 1024000
  }
}
```

#### `POST /api/webhooks/payments/`
Recibe notificaciones de cambios en pagos.

#### `POST /api/webhooks/users/`
Recibe notificaciones de cambios en usuarios.

#### `POST /api/webhooks/attendance/`
Recibe notificaciones de cambios en asistencias.

#### `POST /api/webhooks/generic/`
Webhook genérico para eventos personalizados.

### 🏥 **Salud del Sistema**

#### `GET /api/health/`
Estado de salud del microservicio.

#### `GET /api/system-info/` (Admin)
Información detallada del sistema.

## Middleware de Auditoría

### AuditoriaMiddleware

Registra automáticamente todas las requests HTTP:

```python
# settings.py
MIDDLEWARE = [
    # ... otros middleware
    'auditoria_app.middleware.AuditoriaMiddleware',
]

# Configuración
AUDITORIA_CONFIG = {
    'ENABLE_MIDDLEWARE': True,
    'LOG_ANONYMOUS_USERS': False,
    'EXCLUDE_PATHS': ['/health/', '/static/'],
    'EXCLUDE_METHODS': ['OPTIONS'],
    'LOG_REQUEST_BODY': True,
    'MAX_BODY_LENGTH': 10000,
}
```

### Observer Pattern

Para notificar cambios desde otros microservicios:

```python
from auditoria_app.middleware.observer import notifier

# En otros microservicios
notifier.notify_document_change(
    action='CREATE',
    document_id='doc_123',
    user_id=request.user.id,
    details={'filename': 'test.pdf'}
)
```

## Modelo de Datos

### ActividadSistema

Modelo principal para registro de actividades:

```sql
CREATE TABLE auditoria_app_actividadsistema (
    id CHAR(32) PRIMARY KEY,                    -- UUID
    usuario_id INT,                             -- ID del usuario
    usuario_email VARCHAR(255),                 -- Email del usuario
    accion VARCHAR(20) NOT NULL,                -- CREATE, READ, UPDATE, etc.
    recurso VARCHAR(50) NOT NULL,               -- USERS, DOCUMENTS, etc.
    recurso_id VARCHAR(255),                    -- ID del recurso específico
    detalle JSON,                               -- Detalles adicionales
    fecha_hora DATETIME(6) NOT NULL,            -- Timestamp
    ip_address VARCHAR(45),                     -- IP del cliente
    user_agent TEXT,                            -- User Agent
    session_id VARCHAR(255),                    -- ID de sesión
    exito BOOLEAN NOT NULL DEFAULT TRUE,        -- Si fue exitosa
    codigo_estado INT,                          -- HTTP status code
    mensaje_error TEXT,                         -- Mensaje de error si aplica
    duracion_ms INT,                            -- Duración en milisegundos  
    microservicio VARCHAR(50),                  -- Microservicio origen
    criticidad VARCHAR(20),                     -- LOW, MEDIUM, HIGH, CRITICAL
    context JSON,                               -- Contexto adicional
    tags JSON                                   -- Tags para categorización
);
```

### Índices para Performance

```sql
-- Índices principales
CREATE INDEX idx_usuario_fecha ON auditoria_app_actividadsistema(usuario_id, fecha_hora);
CREATE INDEX idx_accion_fecha ON auditoria_app_actividadsistema(accion, fecha_hora);
CREATE INDEX idx_recurso_fecha ON auditoria_app_actividadsistema(recurso, fecha_hora);
CREATE INDEX idx_microservicio_fecha ON auditoria_app_actividadsistema(microservicio, fecha_hora);
CREATE INDEX idx_exito_fecha ON auditoria_app_actividadsistema(exito, fecha_hora);
CREATE INDEX idx_criticidad ON auditoria_app_actividadsistema(criticidad);
CREATE INDEX idx_ip_fecha ON auditoria_app_actividadsistema(ip_address, fecha_hora);
```

## Comandos de Gestión

### Generar Datos de Prueba

```bash
# Generar 1000 registros para los últimos 30 días
python manage.py seed_auditoria --cantidad 1000 --dias 30

# Limpiar datos existentes y generar nuevos
python manage.py seed_auditoria --cantidad 500 --limpiar
```

### Limpiar Logs Antiguos

```bash
# Eliminar logs de más de 90 días
python manage.py limpiar_logs --dias 90

# Simulación sin eliminar datos
python manage.py limpiar_logs --dias 90 --dry-run

# Mantener logs críticos
python manage.py limpiar_logs --dias 90 --keep-critical
```

## Configuración de Otros Microservicios

### Integración con AuditNotifier

En otros microservicios, agregar el cliente de auditoría:

```python
# settings.py
AUDIT_SERVICE_URL = 'http://localhost:3007'

# views.py o services.py
from auditoria_app.middleware.observer import AuditNotifier

notifier = AuditNotifier()

# Notificar cambios
def create_document(request):
    # ... lógica de creación
    
    notifier.notify_document_change(
        action='CREATE',
        document_id=document.id,
        user_id=request.user.id,
        details={
            'filename': document.filename,
            'size': document.size
        }
    )
```

### Middleware en Otros Servicios

Para registrar automáticamente las actividades:

```python
# En otros microservicios
MIDDLEWARE = [
    # ... otros middleware
    'auditoria_app.middleware.AuditoriaMiddleware',
]
```

## Monitoreo y Alertas

### Actividades Sospechosas

El sistema detecta automáticamente:
- Múltiples intentos de login fallidos
- Descargas masivas de documentos
- Accesos desde IPs inusuales
- Actividades fuera de horario
- Cambios críticos en el sistema

### Métricas de Rendimiento

- Requests por segundo
- Tiempo de respuesta promedio
- Percentiles de latencia (P95, P99)
- Tasa de errores
- Usuarios más activos
- Endpoints más lentos

## Seguridad

### Configuraciones de Seguridad

```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://pontificia.edu",
]
```

### Retención de Datos

- Logs estándar: 90 días
- Logs críticos: 365 días
- Logs de seguridad: 2 años
- Limpieza automática configurable

## Testing

### Ejecutar Pruebas

```bash
# Todas las pruebas
python manage.py test

# Pruebas específicas
python manage.py test auditoria_app.tests.AuditoriaServiceTest

# Con coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Tipos de Pruebas

- **Unit Tests**: Modelos, servicios, repositorios
- **Integration Tests**: API endpoints, middleware
- **Webhook Tests**: Notificaciones externas
- **Performance Tests**: Carga y stress testing

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3007

CMD ["python", "manage.py", "runserver", "0.0.0.0:3007"]
```

### Variables de Entorno Producción

```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key
MYSQL_HOST=db.pontificia.edu
MYSQL_PORT=3306
MYSQL_DATABASE=auditoria_prod
MYSQL_USER=auditoria_prod
MYSQL_PASSWORD=secure-password
AUDIT_RETENTION_DAYS=90
AUDIT_CRITICAL_RETENTION_DAYS=365
```

## Troubleshooting

### Problemas Comunes

1. **Alto uso de memoria**: Ajustar `AUDIT_BATCH_SIZE` y limpiar logs antiguos
2. **Lentitud en consultas**: Verificar índices y usar filtros específicos
3. **Webhooks fallando**: Verificar conectividad y formato de payload
4. **Middleware no registra**: Verificar orden en `MIDDLEWARE` setting

### Logs de Debug

```python
# settings.py
LOGGING = {
    'loggers': {
        'audit': {
            'level': 'DEBUG',
            'handlers': ['file'],
        }
    }
}
```

## Contribución

1. Fork del repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Proyecto académico - Universidad Pontificia

---

## Contacto

**Equipo de Desarrollo Sistema Pontificia**
- Email: desarrollo@pontificia.edu
- Documentación: [Wiki del proyecto]
- Issues: [GitHub Issues]